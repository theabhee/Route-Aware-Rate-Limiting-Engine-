import time
import asyncio
from typing import Dict, Tuple
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.routing import Match


RATE_LIMIT_RULES = {
    ("free", "ai"): {"limit": 5, "window": 60},
    ("free", "read"): {"limit": 30, "window": 60},
    ("paid", "ai"): {"limit": 30, "window": 60},
    ("paid", "read"): {"limit": 120, "window": 60},
}

app = FastAPI()

usage_store: Dict[Tuple[str, str, str], Dict[str, any]] = {}
store_lock = asyncio.Lock()


@app.middleware("http")
async def rate_limiter_middleware(request: Request, call_next):
    # 1. Identify User 
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # 2. Identify Tier 
    tier = request.headers.get("X-User-Tier", "free").lower()
    if tier not in ["free", "paid"]:
        tier = "free"  # Invalid tier falls back to free

    # 3. Identify Endpoint Type from Route configuration tags
    endpoint_type = None
    for route in app.routes:
        
        if hasattr(route, "openapi_extra") and route.openapi_extra:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                endpoint_type = route.openapi_extra.get("endpoint_type")
                break

    # If the endpoint doesn't have rate-limiting tag
    if not endpoint_type:
        return await call_next(request)

    
    rule = RATE_LIMIT_RULES.get((tier, endpoint_type))
    if not rule:
        return await call_next(request)

    limit = rule["limit"]
    window_seconds = rule["window"]
    now = time.time()
    
    # Define tracking key
    tracking_key = (client_ip, tier, endpoint_type)
    
    # Rate Limiting Logic 
    async with store_lock: 
        if tracking_key not in usage_store:
            # First request
            usage_store[tracking_key] = {"count": 1, "window_start": now}
        else:
            state = usage_store[tracking_key]
            elapsed = now - state["window_start"]
            
            if elapsed >= window_seconds:
                # Window has elapsed Completely reset counter
                usage_store[tracking_key] = {"count": 1, "window_start": now}
            else:
                
                if state["count"] >= limit:
                    retry_after = max(0, int(window_seconds - elapsed))
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "rate_limit_exceeded",
                            "limit": limit,
                            "window_seconds": window_seconds,
                            "retry_after_seconds": retry_after
                        }
                    )
                
                # Within limits, increment counter
                state["count"] += 1

    # Request passed validation
    
    response = await call_next(request)
    return response


# Routes to Expose 

@app.post("/ai/generate", openapi_extra={"endpoint_type": "ai"})
async def ai_generate():
    return {"ok": True}

@app.post("/ai/summarise", openapi_extra={"endpoint_type": "ai"})
async def ai_summarise():
    return {"ok": True}

@app.get("/data/list", openapi_extra={"endpoint_type": "read"})
async def data_list():
    return {"ok": True}

@app.get("/data/export", openapi_extra={"endpoint_type": "read"})
async def data_export():
    return {"ok": True}
# The in-memory tracking store
# Key format: (client_ip, tier, endpoint_type)
# Value format: {"count": int, "window_start": float}
usage_store: Dict[Tuple[str, str, str], Dict[str, any]] = {}

app = FastAPI()
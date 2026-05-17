# Context-Aware Rate Limiter

## Server Link: https://rate-limiter-ooln.onrender.com
## How to Run It
1. Make sure you have the required packages installed:
   `pip install fastapi uvicorn`
2. Start the local server:
   `uvicorn main:app --reload`
3. The server will be running at `https://rate-limiter-ooln.onrender.com`. You can use the `test.py` script to simulate traffic.

---

## How I Built It (Design Decisions)

### 1. Using FastAPI and Route Tags
I used FastAPI that lets you attach custom metadata tags directly to the route definitions. When a request comes in, the middleware just looks at the route's tag to see if it's an `"ai"` or `"read"` endpoint.

### 2. The Rate Limiting Algorithm (Fixed Window)
I used a **Fixed Window Counter** algorithm to track user requests. 
When a user makes their first request, the server logs the exact time and starts a 60-second timer. It counts every request they make inside that 60-second window. The moment the 60 seconds are up, their count is completely wiped back to zero, and the timer starts over. 
* **Why this approach?**  as mentioned under Requirements section under 2nd point, 2nd subpoint (Each key has a request count and a window start timestamp. Reset the count when the window has elapsed.)

### 3. Handling Concurrent Users (The Async Lock)
Because FastAPI processes requests asynchronously, there was a risk of a "race condition." If 50 requests hit the server at the exact same millisecond, they might all read the counter at the same time, see a count of `1`, and all update it to `2`—completely bypassing the rate limit. 
To prevent this, I wrapped the counting logic inside an `asyncio.Lock()`. This forces simultaneous requests to form a quick line and update the counter one at a time.
---

## Limitations and Trade-offs

Because this project is built entirely in-memory to meet the assignment constraints, there are a few specific edge cases and limitations :

1. **The "Boundary Burst" Problem:** The Fixed Window algorithm is vulnerable to traffic spikes at the exact moment the timer resets. For example, a free user is allowed 5 AI requests per 60 seconds. They could send 5 requests at the 0:59 second mark. One second later (at 1:00), their timer resets, and they immediately send 5 more requests. They just successfully fired off 10 requests in a 2-second period. In a massive production system, a more complex algorithm (like a Sliding Window) would be used to smooth this out.

2. **Data Wipes on Restart:**
   Because all the tracking data lives in a standard Python dictionary (`usage_store`), everything is stored in the server's RAM. If the server restarts or crashes, all user rate limits are instantly wiped clean.

3. **Memory Growth:**
   Right now, every time a new IP address hits the API, it gets permanently added to the dictionary. In a real-world scenario where a server runs for months, this dictionary would eventually eat up all the server's RAM. To fix this for production, we would need to write a background task that loops through the dictionary every few minutes and deletes old, inactive users.

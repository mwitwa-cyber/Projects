"""
Rate limiting and quota management utilities.
Supports per-user/IP rate limiting, exponential backoff, and quota tracking.
Integrate with API endpoints as needed.
"""
import time
import threading
from collections import defaultdict, deque
from typing import Optional

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.lock = threading.Lock()
        self.requests = defaultdict(deque)  # key: user/IP, value: deque of timestamps

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            q = self.requests[key]
            # Remove timestamps outside the window
            while q and q[0] <= now - self.window_seconds:
                q.popleft()
            if len(q) < self.max_requests:
                q.append(now)
                return True
            return False

    def get_remaining(self, key: str) -> int:
        now = time.time()
        with self.lock:
            q = self.requests[key]
            while q and q[0] <= now - self.window_seconds:
                q.popleft()
            return max(0, self.max_requests - len(q))

class ExponentialBackoff:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.attempts = defaultdict(int)

    def get_delay(self, key: str) -> float:
        attempt = self.attempts[key]
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        self.attempts[key] += 1
        return delay

    def reset(self, key: str):
        self.attempts[key] = 0

class QuotaManager:
    def __init__(self, quota: int):
        self.quota = quota
        self.usage = defaultdict(int)
        self.lock = threading.Lock()

    def consume(self, key: str, amount: int = 1) -> bool:
        with self.lock:
            if self.usage[key] + amount <= self.quota:
                self.usage[key] += amount
                return True
            return False

    def get_remaining(self, key: str) -> int:
        with self.lock:
            return max(0, self.quota - self.usage[key])

    def reset(self, key: str):
        with self.lock:
            self.usage[key] = 0

# Example usage:
# limiter = RateLimiter(max_requests=100, window_seconds=60)
# if not limiter.is_allowed(user_id):
#     return {"error": "Rate limit exceeded"}, 429
#
# backoff = ExponentialBackoff()
# delay = backoff.get_delay(user_id)
# time.sleep(delay)
# backoff.reset(user_id)
#
# quota = QuotaManager(quota=1000)
# if not quota.consume(user_id, 10):
#     return {"error": "Quota exceeded"}, 429

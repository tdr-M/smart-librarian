import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, limit: int = 30, window_s: int = 60):
        self.limit = limit
        self.window = window_s
        self._buckets = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self._buckets[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
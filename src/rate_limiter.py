"""Simple rate limiter implementations for tests."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = max(0, capacity)
        self.refill_rate = max(0.0, refill_rate)
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        if elapsed > 0 and self.refill_rate > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

    def consume(self, amount: int = 1) -> bool:
        if amount <= 0:
            return True
        self._refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def get_remaining_tokens(self) -> int:
        self._refill()
        return int(self.tokens)


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_size: float):
        self.max_requests = max(0, max_requests)
        self.window_size = max(0.0, window_size)
        self.requests: Deque[float] = deque()

    def _purge(self) -> None:
        cutoff = time.time() - self.window_size
        while self.requests and self.requests[0] <= cutoff:
            self.requests.popleft()

    def is_allowed(self) -> bool:
        self._purge()
        if len(self.requests) < self.max_requests:
            self.requests.append(time.time())
            return True
        return False

    def get_remaining_requests(self) -> int:
        self._purge()
        return max(0, self.max_requests - len(self.requests))


class RateLimitManager:
    def __init__(self, default_capacity: int = 100, default_refill_rate: float = 1.0):
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.limiters: Dict[str, RateLimiter] = {}

    def get_limiter(self, client_id: str) -> RateLimiter:
        if client_id not in self.limiters:
            self.limiters[client_id] = RateLimiter(self.default_capacity, self.default_refill_rate)
        return self.limiters[client_id]

    def is_allowed(self, client_id: str, amount: int = 1) -> bool:
        return self.get_limiter(client_id).consume(amount)

    def get_client_status(self, client_id: str) -> Dict[str, float]:
        limiter = self.get_limiter(client_id)
        return {
            "remaining_tokens": limiter.get_remaining_tokens(),
            "capacity": limiter.capacity,
            "refill_rate": limiter.refill_rate,
        }

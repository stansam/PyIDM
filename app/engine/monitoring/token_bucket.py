"""Token bucket bandwidth throttling implementation."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """Thread-safe token bucket rate limiter for download bandwidth throttling."""

    def __init__(self, rate_bps: float, burst_factor: float = 2.0) -> None:
        self.rate = rate_bps
        self.capacity = rate_bps * burst_factor
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, num_bytes: int) -> None:
        """Consume tokens, blocking if insufficient tokens are available."""
        if self.rate <= 0:
            return  # Unlimited

        sleep_time = 0.0
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))

            if num_bytes > self.tokens:
                deficit = num_bytes - self.tokens
                sleep_time = deficit / self.rate
                self.tokens = 0.0
                self.last_refill = time.monotonic()
            else:
                self.tokens -= num_bytes

        # Sleep OUTSIDE the lock to prevent blocking other worker threads
        if sleep_time > 0.0:
            time.sleep(sleep_time)

    def set_rate(self, rate_bps: float) -> None:
        """Dynamically update target transfer rate."""
        with self._lock:
            self.rate = rate_bps
            self.capacity = rate_bps * 2.0
            self.tokens = min(self.tokens, self.capacity)


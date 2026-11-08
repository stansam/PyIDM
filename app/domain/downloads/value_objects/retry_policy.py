"""Retry policy value object with exponential backoff and jitter."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Configurable exponential backoff policy for transient network failures."""

    max_attempts: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True

    def delay_for_attempt(self, attempt: int) -> float:
        """Calculate wait delay in seconds for the given retry attempt (1-based)."""
        if attempt <= 1:
            delay = self.base_delay_seconds
        else:
            delay = self.base_delay_seconds * (self.multiplier ** (attempt - 1))

        delay = min(delay, self.max_delay_seconds)

        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay


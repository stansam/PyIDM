"""Rolling window download speed calculator using monotonic timestamps."""

from __future__ import annotations

import time
from collections import deque
from threading import Lock

from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.shared.constants import SPEED_WINDOW_SECONDS


class RollingSpeedMeter:
    """Thread-safe rolling window speed calculator immune to NTP clock skew."""

    def __init__(self, window_seconds: float = SPEED_WINDOW_SECONDS) -> None:
        self.window = window_seconds
        self._samples: deque[tuple[float, int]] = deque()
        self._lock = Lock()

    def update(self, byte_count: int) -> DownloadSpeed:
        """Record received bytes and return current speed."""
        now = time.monotonic()
        cutoff = now - self.window

        with self._lock:
            self._samples.append((now, byte_count))

            while self._samples and self._samples[0][0] < cutoff:
                self._samples.popleft()

            if len(self._samples) < 2:
                return DownloadSpeed(0.0)

            oldest = self._samples[0][0]
            elapsed = now - oldest
            if elapsed <= 0.0:
                return DownloadSpeed(0.0)

            total_bytes = sum(b for _, b in self._samples)
            return DownloadSpeed(total_bytes / elapsed)

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()


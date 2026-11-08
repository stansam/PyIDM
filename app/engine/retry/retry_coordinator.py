"""Error classification and retry coordination for network resilience."""

from __future__ import annotations

import threading
import time

import httpx

from app.domain.downloads.enums.failure_category import FailureCategory
from app.domain.downloads.value_objects.retry_policy import RetryPolicy


class ErrorClassifier:
    """Categorizes exceptions into FailureCategory for retry determination."""

    @staticmethod
    def classify(exc: Exception) -> FailureCategory:
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, TimeoutError)):
            return FailureCategory.TRANSIENT_NETWORK
        if isinstance(exc, httpx.HTTPStatusError):
            code = exc.response.status_code
            if code == 429:
                return FailureCategory.RATE_LIMITED
            if code in (401, 403):
                return FailureCategory.AUTHENTICATION
            if code in (404, 410):
                return FailureCategory.NOT_FOUND
            if code == 416:
                return FailureCategory.RANGE_REJECTED
            if code >= 500:
                return FailureCategory.SERVER_ERROR
        if isinstance(exc, OSError):
            # Check for disk full (Windows / POSIX error codes)
            err_no = getattr(exc, "errno", None)
            if err_no == 28 or "no space left on device" in str(exc).lower():
                return FailureCategory.DISK_FULL
            if err_no == 13 or "permission denied" in str(exc).lower():
                return FailureCategory.PERMISSION_DENIED

        return FailureCategory.UNKNOWN


class RetryCoordinator:
    """Coordinates exponential backoff delays with cooperative cancellation checks."""

    def __init__(self, cancel_event: threading.Event) -> None:
        self._cancel_event = cancel_event

    def is_retryable(self, category: FailureCategory) -> bool:
        """Return True if the failure category represents a transient retryable condition."""
        return category in (
            FailureCategory.TRANSIENT_NETWORK,
            FailureCategory.SERVER_ERROR,
            FailureCategory.RATE_LIMITED,
            FailureCategory.UNKNOWN,
        )

    def wait_backoff(
        self, attempt: int, policy: RetryPolicy, retry_after_sec: float | None = None
    ) -> bool:
        """Sleep for calculated delay while checking cancel_event. Returns False if cancelled."""
        if self._cancel_event.is_set():
            return False

        delay = retry_after_sec if retry_after_sec is not None else policy.delay_for_attempt(attempt)
        step = 0.1
        elapsed = 0.0

        while elapsed < delay:
            if self._cancel_event.is_set():
                return False
            time.sleep(min(step, delay - elapsed))
            elapsed += step

        return not self._cancel_event.is_set()

"""Domain exception hierarchy for PyIDM."""

from __future__ import annotations


class PyIDMDomainError(Exception):
    """Base exception for all domain logic violations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidTransitionError(PyIDMDomainError):
    """Raised when an illegal state machine transition is attempted."""

    def __init__(self, current_state: str, attempted_state: str) -> None:
        super().__init__(
            f"Invalid state transition from '{current_state}' to '{attempted_state}'"
        )
        self.current_state = current_state
        self.attempted_state = attempted_state


class InvalidUrlError(PyIDMDomainError):
    """Raised when a download URL is invalid or uses an unsupported scheme."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"Invalid download URL '{url}': {reason}")
        self.url = url
        self.reason = reason


class InvalidSegmentError(PyIDMDomainError):
    """Raised when segment offsets or properties are invalid."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Segment invariant violation: {reason}")


class DownloadNotFoundError(PyIDMDomainError):
    """Raised when a requested download ID does not exist."""

    def __init__(self, download_id: str) -> None:
        super().__init__(f"Download not found: {download_id}")
        self.download_id = download_id


class QueueNotFoundError(PyIDMDomainError):
    """Raised when a requested queue ID does not exist."""

    def __init__(self, queue_id: str) -> None:
        super().__init__(f"Queue not found: {queue_id}")
        self.queue_id = queue_id


class InvalidFilenameError(PyIDMDomainError):
    """Raised when a filename contains illegal characters or path traversal."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(f"Invalid destination filename '{filename}': {reason}")
        self.filename = filename
        self.reason = reason


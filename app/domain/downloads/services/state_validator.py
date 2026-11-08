"""Domain service enforcing strict download state transitions."""

from __future__ import annotations

from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.exceptions.domain_errors import InvalidTransitionError

# Valid transition rule table
_VALID_TRANSITIONS: dict[DownloadStatus, frozenset[DownloadStatus]] = {
    DownloadStatus.PENDING: frozenset(
        {DownloadStatus.INSPECTING, DownloadStatus.QUEUED, DownloadStatus.CANCELLED}
    ),
    DownloadStatus.QUEUED: frozenset(
        {DownloadStatus.INSPECTING, DownloadStatus.DOWNLOADING, DownloadStatus.CANCELLED}
    ),
    DownloadStatus.INSPECTING: frozenset(
        {
            DownloadStatus.QUEUED,
            DownloadStatus.DOWNLOADING,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        }
    ),
    DownloadStatus.DOWNLOADING: frozenset(
        {
            DownloadStatus.PAUSING,
            DownloadStatus.VERIFYING,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        }
    ),
    DownloadStatus.PAUSING: frozenset(
        {DownloadStatus.PAUSED, DownloadStatus.FAILED}
    ),
    DownloadStatus.PAUSED: frozenset(
        {DownloadStatus.RESUMING, DownloadStatus.CANCELLED}
    ),
    DownloadStatus.RESUMING: frozenset(
        {
            DownloadStatus.DOWNLOADING,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        }
    ),
    DownloadStatus.VERIFYING: frozenset(
        {DownloadStatus.ASSEMBLING, DownloadStatus.FAILED}
    ),
    DownloadStatus.ASSEMBLING: frozenset(
        {DownloadStatus.COMPLETED, DownloadStatus.FAILED}
    ),
    DownloadStatus.COMPLETED: frozenset(),  # Terminal
    DownloadStatus.FAILED: frozenset(
        {DownloadStatus.PENDING}  # Manual retry resets to PENDING
    ),
    DownloadStatus.CANCELLED: frozenset(),  # Terminal
}


class DownloadStateValidator:
    """Validates state machine transitions against defined invariants."""

    @staticmethod
    def validate(current: DownloadStatus, next_state: DownloadStatus) -> None:
        """Raise InvalidTransitionError if transition is illegal."""
        allowed = _VALID_TRANSITIONS.get(current, frozenset())
        if next_state not in allowed:
            raise InvalidTransitionError(current.value, next_state.value)

    @staticmethod
    def valid_next_states(current: DownloadStatus) -> frozenset[DownloadStatus]:
        """Return all legal states that can follow the current state."""
        return _VALID_TRANSITIONS.get(current, frozenset())


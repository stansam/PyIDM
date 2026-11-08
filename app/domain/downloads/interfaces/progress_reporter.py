"""Engine reporting protocols for progress, status, and error notifications."""

from __future__ import annotations

from typing import Protocol

from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import DownloadId, SegmentId
from app.domain.downloads.value_objects.progress import DownloadProgress


class ProgressReporter(Protocol):
    """Protocol implemented by application signal adapters to receive engine progress."""

    def report_progress(self, download_id: DownloadId, progress: DownloadProgress) -> None:
        """Report throttled aggregate download progress."""
        ...

    def report_segment_progress(
        self, download_id: DownloadId, segment_id: SegmentId, bytes_written: int
    ) -> None:
        """Report raw bytes received by a specific worker."""
        ...

    def report_status_change(
        self, download_id: DownloadId, new_status: DownloadStatus
    ) -> None:
        """Report a validated lifecycle transition."""
        ...

    def report_error(self, download_id: DownloadId, error_message: str) -> None:
        """Report an unrecoverable failure event."""
        ...


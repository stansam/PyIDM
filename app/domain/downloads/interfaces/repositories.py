"""Abstract repository protocols for download and segment domain models."""

from __future__ import annotations

from typing import Protocol

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import DownloadId


class DownloadRepository(Protocol):
    """Protocol for Download entity persistence operations."""

    def save(self, download: Download) -> None:
        """Create or update a Download entity."""
        ...

    def get_by_id(self, download_id: DownloadId) -> Download | None:
        """Retrieve a Download by unique identifier."""
        ...

    def get_all(self) -> list[Download]:
        """Retrieve all downloads ordered by creation date descending."""
        ...

    def get_by_status(self, status: DownloadStatus) -> list[Download]:
        """Retrieve all downloads matching the specified lifecycle state."""
        ...

    def get_active(self) -> list[Download]:
        """Retrieve all downloads currently in an active or non-terminal state."""
        ...

    def update_status(self, download_id: DownloadId, status: DownloadStatus) -> None:
        """Update only the status column of a download."""
        ...

    def delete(self, download_id: DownloadId) -> None:
        """Permanently delete a download record and its cascaded segments."""
        ...


class SegmentRepository(Protocol):
    """Protocol for DownloadSegment persistence operations."""

    def save_all(self, segments: list[DownloadSegment]) -> None:
        """Batch save or update segments."""
        ...

    def get_by_download_id(self, download_id: DownloadId) -> list[DownloadSegment]:
        """Retrieve all segments for a given parent download ordered by segment_index."""
        ...

    def update_segment(self, segment: DownloadSegment) -> None:
        """Update downloaded bytes and status for an individual segment."""
        ...

    def delete_by_download_id(self, download_id: DownloadId) -> None:
        """Purge all segments associated with a parent download."""
        ...


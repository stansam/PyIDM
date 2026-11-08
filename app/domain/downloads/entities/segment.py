"""Download segment entity representing one byte-range chunk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.domain.downloads.enums.segment_status import SegmentStatus
from app.domain.downloads.value_objects.byte_range import ByteRange
from app.domain.downloads.value_objects.ids import DownloadId, SegmentId


@dataclass
class DownloadSegment:
    """Represents a discrete byte range slice within a segmented download."""

    id: SegmentId
    download_id: DownloadId
    segment_index: int
    byte_range: ByteRange
    status: SegmentStatus = SegmentStatus.PENDING
    downloaded_bytes: int = 0
    temp_file_path: Path | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def current_offset(self) -> int:
        """The absolute byte offset where the next chunk will be written."""
        return self.byte_range.start + self.downloaded_bytes

    @property
    def remaining_bytes(self) -> int:
        """Remaining bytes to be downloaded for this segment."""
        return max(0, self.byte_range.length - self.downloaded_bytes)

    @property
    def is_complete(self) -> bool:
        """True if all bytes in this byte range have been downloaded."""
        return self.downloaded_bytes >= self.byte_range.length

    def record_progress(self, bytes_written: int) -> None:
        """Increment downloaded byte count atomically within this segment."""
        self.downloaded_bytes += bytes_written
        if self.is_complete:
            self.status = SegmentStatus.COMPLETED
            self.completed_at = datetime.now(UTC)

    def mark_completed(self, completed_at: datetime | None = None) -> None:
        self.downloaded_bytes = self.byte_range.length
        self.status = SegmentStatus.COMPLETED
        self.completed_at = completed_at or datetime.now(UTC)

    def mark_failed(self) -> None:
        self.status = SegmentStatus.FAILED


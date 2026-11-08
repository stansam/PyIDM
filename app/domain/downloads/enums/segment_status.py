"""Download segment status enum."""

from enum import StrEnum


class SegmentStatus(StrEnum):
    """Lifecycle states for a single byte-range segment."""

    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


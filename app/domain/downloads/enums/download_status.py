"""Download lifecycle status enum."""

from enum import StrEnum


class DownloadStatus(StrEnum):
    """Formal lifecycle states for a download entity."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    INSPECTING = "INSPECTING"
    DOWNLOADING = "DOWNLOADING"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    VERIFYING = "VERIFYING"
    ASSEMBLING = "ASSEMBLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


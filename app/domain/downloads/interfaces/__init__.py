"""Domain interfaces package exports."""

from app.domain.downloads.interfaces.progress_reporter import ProgressReporter
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)

__all__ = [
    "DownloadRepository",
    "SegmentRepository",
    "ProgressReporter",
]


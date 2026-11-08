"""Domain enums exports."""

from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.enums.failure_category import FailureCategory
from app.domain.downloads.enums.segment_status import SegmentStatus
from app.domain.downloads.enums.strategy import DownloadStrategy

__all__ = [
    "DownloadStatus",
    "SegmentStatus",
    "DownloadStrategy",
    "FailureCategory",
    "DownloadCategory",
]


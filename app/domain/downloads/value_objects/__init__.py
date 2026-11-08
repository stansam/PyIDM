"""Domain value objects exports."""

from app.domain.downloads.value_objects.byte_range import ByteRange
from app.domain.downloads.value_objects.file_size import FileSize
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import (
    DownloadId,
    QueueId,
    SegmentId,
    create_download_id,
    create_queue_id,
    create_segment_id,
    parse_download_id,
    parse_queue_id,
    parse_segment_id,
)
from app.domain.downloads.value_objects.progress import DownloadProgress
from app.domain.downloads.value_objects.retry_policy import RetryPolicy
from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.domain.downloads.value_objects.url import DownloadUrl

__all__ = [
    "DownloadId",
    "SegmentId",
    "QueueId",
    "create_download_id",
    "create_segment_id",
    "create_queue_id",
    "parse_download_id",
    "parse_segment_id",
    "parse_queue_id",
    "ByteRange",
    "DownloadSpeed",
    "FileSize",
    "DownloadUrl",
    "HttpHeaders",
    "RetryPolicy",
    "DownloadProgress",
]


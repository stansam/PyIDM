"""Typed identifier value objects for domain aggregates."""

from __future__ import annotations

import uuid
from typing import NewType

DownloadId = NewType("DownloadId", uuid.UUID)
SegmentId = NewType("SegmentId", uuid.UUID)
QueueId = NewType("QueueId", uuid.UUID)


def create_download_id() -> DownloadId:
    """Generate a new unique DownloadId."""
    return DownloadId(uuid.uuid4())


def create_segment_id() -> SegmentId:
    """Generate a new unique SegmentId."""
    return SegmentId(uuid.uuid4())


def create_queue_id() -> QueueId:
    """Generate a new unique QueueId."""
    return QueueId(uuid.uuid4())


def parse_download_id(val: str) -> DownloadId:
    """Parse a UUID string into a DownloadId."""
    return DownloadId(uuid.UUID(val))


def parse_segment_id(val: str) -> SegmentId:
    """Parse a UUID string into a SegmentId."""
    return SegmentId(uuid.UUID(val))


def parse_queue_id(val: str) -> QueueId:
    """Parse a UUID string into a QueueId."""
    return QueueId(uuid.UUID(val))


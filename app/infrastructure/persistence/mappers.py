"""Mappers converting between SQLAlchemy ORM models and pure domain entities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.enums.failure_category import FailureCategory
from app.domain.downloads.enums.segment_status import SegmentStatus
from app.domain.downloads.enums.strategy import DownloadStrategy
from app.domain.downloads.value_objects.byte_range import ByteRange
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import (
    parse_download_id,
    parse_queue_id,
    parse_segment_id,
)
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.persistence.models import DownloadModel, DownloadSegmentModel
from app.shared.types import Priority


class ModelMapper:
    """Bidirectional mapping between Domain Entities and SQLAlchemy Models."""

    @staticmethod
    def to_download_model(entity: Download) -> DownloadModel:
        return DownloadModel(
            id=str(entity.id),
            url=entity.url.raw,
            destination_directory=str(entity.destination_directory),
            filename=entity.filename,
            status=entity.status.value,
            strategy=entity.strategy.value if entity.strategy else None,
            total_size=entity.total_size,
            downloaded_bytes=entity.downloaded_bytes,
            connection_count=entity.connection_count,
            priority=int(entity.priority),
            category=entity.category.value,
            queue_id=str(entity.queue_id) if entity.queue_id else None,
            etag=entity.etag,
            last_modified=entity.last_modified,
            content_type=entity.content_type,
            custom_headers=json.dumps(entity.custom_headers.to_dict()),
            error_message=entity.error_message,
            error_category=entity.error_category.value if entity.error_category else None,
            speed_limit_bps=entity.speed_limit_bps,
            created_at=int(entity.created_at.timestamp() * 1000),
            started_at=int(entity.started_at.timestamp() * 1000) if entity.started_at else None,
            completed_at=int(entity.completed_at.timestamp() * 1000)
            if entity.completed_at
            else None,
        )

    @staticmethod
    def to_download_entity(model: DownloadModel) -> Download:
        headers_dict: dict[str, str] = {}
        if model.custom_headers:
            try:
                headers_dict = json.loads(model.custom_headers)
            except Exception:
                headers_dict = {}

        return Download(
            id=parse_download_id(model.id),
            url=DownloadUrl.parse(model.url),
            destination_directory=Path(model.destination_directory),
            filename=model.filename,
            status=DownloadStatus(model.status),
            strategy=DownloadStrategy(model.strategy) if model.strategy else None,
            total_size=model.total_size,
            downloaded_bytes=model.downloaded_bytes,
            connection_count=model.connection_count,
            priority=Priority(model.priority),
            category=DownloadCategory(model.category),
            queue_id=parse_queue_id(model.queue_id) if model.queue_id else None,
            custom_headers=HttpHeaders(headers_dict),
            etag=model.etag,
            last_modified=model.last_modified,
            content_type=model.content_type,
            error_message=model.error_message,
            error_category=FailureCategory(model.error_category)
            if model.error_category
            else None,
            speed_limit_bps=model.speed_limit_bps,
            created_at=datetime.fromtimestamp(model.created_at / 1000.0),
            started_at=datetime.fromtimestamp(model.started_at / 1000.0)
            if model.started_at
            else None,
            completed_at=datetime.fromtimestamp(model.completed_at / 1000.0)
            if model.completed_at
            else None,
        )

    @staticmethod
    def to_segment_model(entity: DownloadSegment) -> DownloadSegmentModel:
        return DownloadSegmentModel(
            id=str(entity.id),
            download_id=str(entity.download_id),
            segment_index=entity.segment_index,
            start_byte=entity.byte_range.start,
            end_byte=entity.byte_range.end,
            downloaded_bytes=entity.downloaded_bytes,
            status=entity.status.value,
            temp_file_path=str(entity.temp_file_path) if entity.temp_file_path else None,
            retry_count=entity.retry_count,
            started_at=int(entity.started_at.timestamp() * 1000) if entity.started_at else None,
            completed_at=int(entity.completed_at.timestamp() * 1000)
            if entity.completed_at
            else None,
        )

    @staticmethod
    def to_segment_entity(model: DownloadSegmentModel) -> DownloadSegment:
        return DownloadSegment(
            id=parse_segment_id(model.id),
            download_id=parse_download_id(model.download_id),
            segment_index=model.segment_index,
            byte_range=ByteRange(start=model.start_byte, end=model.end_byte),
            status=SegmentStatus(model.status),
            downloaded_bytes=model.downloaded_bytes,
            temp_file_path=Path(model.temp_file_path) if model.temp_file_path else None,
            retry_count=model.retry_count,
            started_at=datetime.fromtimestamp(model.started_at / 1000.0)
            if model.started_at
            else None,
            completed_at=datetime.fromtimestamp(model.completed_at / 1000.0)
            if model.completed_at
            else None,
        )


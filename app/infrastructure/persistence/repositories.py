"""Concrete SQLAlchemy 2.0 implementations of download repositories."""

from __future__ import annotations

from sqlalchemy import delete, desc, select, update
from sqlalchemy.orm import Session, scoped_session

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)
from app.domain.downloads.value_objects.ids import DownloadId
from app.infrastructure.persistence.mappers import ModelMapper
from app.infrastructure.persistence.models import DownloadModel, DownloadSegmentModel


class SqlDownloadRepository(DownloadRepository):
    """SQLAlchemy 2.0 repository for the Download aggregate."""

    def __init__(self, session_factory: scoped_session[Session]) -> None:
        self._session_factory = session_factory

    def save(self, download: Download) -> None:
        model = ModelMapper.to_download_model(download)
        with self._session_factory() as session:
            session.merge(model)
            session.commit()

    def get_by_id(self, download_id: DownloadId) -> Download | None:
        with self._session_factory() as session:
            model = session.get(DownloadModel, str(download_id))
            if model is None:
                return None
            return ModelMapper.to_download_entity(model)

    def get_all(self) -> list[Download]:
        with self._session_factory() as session:
            stmt = select(DownloadModel).order_by(desc(DownloadModel.created_at))
            models = session.scalars(stmt).all()
            return [ModelMapper.to_download_entity(m) for m in models]

    def get_by_status(self, status: DownloadStatus) -> list[Download]:
        with self._session_factory() as session:
            stmt = (
                select(DownloadModel)
                .where(DownloadModel.status == status.value)
                .order_by(desc(DownloadModel.created_at))
            )
            models = session.scalars(stmt).all()
            return [ModelMapper.to_download_entity(m) for m in models]

    def get_active(self) -> list[Download]:
        with self._session_factory() as session:
            stmt = (
                select(DownloadModel)
                .where(
                    DownloadModel.status.in_(
                        [
                            DownloadStatus.DOWNLOADING.value,
                            DownloadStatus.QUEUED.value,
                            DownloadStatus.INSPECTING.value,
                            DownloadStatus.PAUSING.value,
                            DownloadStatus.RESUMING.value,
                            DownloadStatus.VERIFYING.value,
                            DownloadStatus.ASSEMBLING.value,
                        ]
                    )
                )
                .order_by(desc(DownloadModel.created_at))
            )
            models = session.scalars(stmt).all()
            return [ModelMapper.to_download_entity(m) for m in models]

    def update_status(self, download_id: DownloadId, status: DownloadStatus) -> None:
        with self._session_factory() as session:
            stmt = (
                update(DownloadModel)
                .where(DownloadModel.id == str(download_id))
                .values(status=status.value)
            )
            session.execute(stmt)
            session.commit()

    def delete(self, download_id: DownloadId) -> None:
        with self._session_factory() as session:
            stmt = delete(DownloadModel).where(DownloadModel.id == str(download_id))
            session.execute(stmt)
            session.commit()


class SqlSegmentRepository(SegmentRepository):
    """SQLAlchemy 2.0 repository for byte-range segments."""

    def __init__(self, session_factory: scoped_session[Session]) -> None:
        self._session_factory = session_factory

    def save_all(self, segments: list[DownloadSegment]) -> None:
        with self._session_factory() as session:
            for seg in segments:
                model = ModelMapper.to_segment_model(seg)
                session.merge(model)
            session.commit()

    def get_by_download_id(self, download_id: DownloadId) -> list[DownloadSegment]:
        with self._session_factory() as session:
            stmt = (
                select(DownloadSegmentModel)
                .where(DownloadSegmentModel.download_id == str(download_id))
                .order_by(DownloadSegmentModel.segment_index)
            )
            models = session.scalars(stmt).all()
            return [ModelMapper.to_segment_entity(m) for m in models]

    def update_segment(self, segment: DownloadSegment) -> None:
        with self._session_factory() as session:
            stmt = (
                update(DownloadSegmentModel)
                .where(DownloadSegmentModel.id == str(segment.id))
                .values(
                    downloaded_bytes=segment.downloaded_bytes,
                    status=segment.status.value,
                    retry_count=segment.retry_count,
                    completed_at=int(segment.completed_at.timestamp() * 1000)
                    if segment.completed_at
                    else None,
                )
            )
            session.execute(stmt)
            session.commit()

    def delete_by_download_id(self, download_id: DownloadId) -> None:
        with self._session_factory() as session:
            stmt = delete(DownloadSegmentModel).where(
                DownloadSegmentModel.download_id == str(download_id)
            )
            session.execute(stmt)
            session.commit()


"""SQLAlchemy 2.0 declarative database models."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 declarative mappings."""

    pass


class DownloadModel(Base):
    """Database representation of the Download aggregate."""

    __tablename__ = "downloads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    destination_directory: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_size: Mapped[int] = mapped_column(BigInteger, default=-1)
    downloaded_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    connection_count: Mapped[int] = mapped_column(Integer, default=4)
    priority: Mapped[int] = mapped_column(Integer, default=2)
    category: Mapped[str] = mapped_column(String(64), default="OTHER")
    queue_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    custom_headers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    speed_limit_bps: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    completed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    segments: Mapped[list[DownloadSegmentModel]] = relationship(
        "DownloadSegmentModel", back_populates="download", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_downloads_status", "status"),
        Index("ix_downloads_created_at", "created_at"),
        Index("ix_downloads_category", "category"),
        Index(
            "ix_active_downloads",
            "status",
            sqlite_where=text(
                "status IN ('DOWNLOADING', 'QUEUED', 'INSPECTING', 'PAUSING', 'RESUMING')"
            ),
        ),
    )


class DownloadSegmentModel(Base):
    """Database representation of a single byte-range chunk."""

    __tablename__ = "download_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    download_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("downloads.id", ondelete="CASCADE"), nullable=False
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_byte: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_byte: Mapped[int] = mapped_column(BigInteger, nullable=False)
    downloaded_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    temp_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    completed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    download: Mapped[DownloadModel] = relationship("DownloadModel", back_populates="segments")

    __table_args__ = (
        Index("ix_segments_download_id", "download_id"),
        CheckConstraint("start_byte <= end_byte", name="ck_segment_byte_order"),
    )


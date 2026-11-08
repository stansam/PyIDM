"""Download entity representing an active, paused, or completed download aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.enums.failure_category import FailureCategory
from app.domain.downloads.enums.strategy import DownloadStrategy
from app.domain.downloads.services.state_validator import DownloadStateValidator
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import DownloadId, QueueId
from app.domain.downloads.value_objects.progress import DownloadProgress
from app.domain.downloads.value_objects.retry_policy import RetryPolicy
from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.domain.downloads.value_objects.url import DownloadUrl
from app.shared.constants import DEFAULT_CONNECTIONS_PER_DOWNLOAD
from app.shared.types import Priority


@dataclass
class Download:
    """Aggregate root for a download task."""

    id: DownloadId
    url: DownloadUrl
    destination_directory: Path
    filename: str
    status: DownloadStatus = field(default=DownloadStatus.PENDING)
    strategy: DownloadStrategy | None = None
    total_size: int = -1
    downloaded_bytes: int = 0
    connection_count: int = DEFAULT_CONNECTIONS_PER_DOWNLOAD
    priority: Priority = Priority.NORMAL
    category: DownloadCategory = DownloadCategory.OTHER
    queue_id: QueueId | None = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    custom_headers: HttpHeaders = field(default_factory=HttpHeaders)
    speed_limit_bps: int | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None
    error_message: str | None = None
    error_category: FailureCategory | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def transition_to(self, new_status: DownloadStatus) -> None:
        """Validate and apply a state machine transition."""
        DownloadStateValidator.validate(self.status, new_status)
        self.status = new_status

    def mark_failed(self, message: str, category: FailureCategory) -> None:
        self.error_message = message
        self.error_category = category
        self.transition_to(DownloadStatus.FAILED)

    def mark_completed(self, completed_at: datetime | None = None) -> None:
        self.completed_at = completed_at or datetime.now(UTC)
        self.transition_to(DownloadStatus.COMPLETED)

    @property
    def final_path(self) -> Path:
        """Resolved target path for the finished file."""
        return self.destination_directory / self.filename

    @property
    def is_active(self) -> bool:
        """True if the download is actively occupying execution bandwidth."""
        return self.status in (
            DownloadStatus.DOWNLOADING,
            DownloadStatus.PAUSING,
            DownloadStatus.RESUMING,
            DownloadStatus.INSPECTING,
            DownloadStatus.VERIFYING,
            DownloadStatus.ASSEMBLING,
        )

    def to_progress(self, current_speed_bps: float = 0.0) -> DownloadProgress:
        """Create a progress value object snapshot."""
        eta: float | None = None
        if self.total_size > 0 and current_speed_bps > 0:
            remaining = max(0, self.total_size - self.downloaded_bytes)
            eta = remaining / current_speed_bps

        return DownloadProgress(
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_size if self.total_size >= 0 else None,
            speed=DownloadSpeed(current_speed_bps),
            eta_seconds=eta,
        )


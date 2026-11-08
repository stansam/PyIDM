"""Download progress metrics value object."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.downloads.value_objects.speed import DownloadSpeed


@dataclass(frozen=True, slots=True)
class DownloadProgress:
    """Snapshot of transfer metrics for a download."""

    downloaded_bytes: int
    total_bytes: int | None
    speed: DownloadSpeed
    eta_seconds: float | None
    segment_count: int = 1
    completed_segment_count: int = 0

    @property
    def percentage(self) -> float | None:
        if self.total_bytes is None or self.total_bytes <= 0:
            return None
        return min(100.0, max(0.0, (self.downloaded_bytes / self.total_bytes) * 100.0))

    @property
    def is_size_known(self) -> bool:
        return self.total_bytes is not None and self.total_bytes >= 0


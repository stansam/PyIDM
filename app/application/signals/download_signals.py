"""Type-safe Qt signal emitter translating engine callbacks to main thread Qt signals."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import DownloadId, SegmentId
from app.domain.downloads.value_objects.progress import DownloadProgress


class DownloadSignalEmitter(QObject):
    """Bridge between background worker threads and the PySide6 main UI thread."""

    progress_updated = Signal(str, int, int, float, float)
    status_changed = Signal(str, str)
    error_occurred = Signal(str, str)
    download_completed = Signal(str)
    browser_download_requested = Signal(str, str, str, str, int)
    download_added = Signal(str)

    def report_progress(self, download_id: DownloadId, progress: DownloadProgress) -> None:
        total = progress.total_bytes if progress.total_bytes is not None else -1
        eta = progress.eta_seconds if progress.eta_seconds is not None else -1.0
        self.progress_updated.emit(
            str(download_id),
            progress.downloaded_bytes,
            total,
            progress.speed.bytes_per_second,
            eta,
        )

    def report_segment_progress(
        self, download_id: DownloadId, segment_id: SegmentId, bytes_written: int
    ) -> None:
        pass

    def report_status_change(
        self, download_id: DownloadId, new_status: DownloadStatus
    ) -> None:
        self.status_changed.emit(str(download_id), new_status.value)
        if new_status == DownloadStatus.COMPLETED:
            self.download_completed.emit(str(download_id))

    def report_error(self, download_id: DownloadId, error_message: str) -> None:
        self.error_occurred.emit(str(download_id), error_message)

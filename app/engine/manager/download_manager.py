"""High-level download manager coordinating active orchestrators and worker threads."""

from __future__ import annotations

import threading

from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.interfaces.progress_reporter import ProgressReporter
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)
from app.domain.downloads.value_objects.ids import DownloadId
from app.engine.downloader.orchestrator import DownloadOrchestrator
from app.engine.monitoring.token_bucket import TokenBucket
from app.infrastructure.filesystem.manifest_storage import JsonManifestStorage
from app.infrastructure.networking.http_stream_client import HttpStreamClient


class DownloadManager:
    """Central engine manager coordinating downloads, active orchestrators, and concurrency."""

    def __init__(
        self,
        download_repo: DownloadRepository,
        segment_repo: SegmentRepository,
        manifest_storage: JsonManifestStorage,
        http_client: HttpStreamClient,
        progress_reporter: ProgressReporter | None = None,
        max_active_downloads: int = 3,
        global_speed_limit_bps: int | None = None,
    ) -> None:
        self.download_repo = download_repo
        self.segment_repo = segment_repo
        self.manifest_storage = manifest_storage
        self.http_client = http_client
        self.progress_reporter = progress_reporter
        self.max_active_downloads = max_active_downloads

        self._active_orchestrators: dict[DownloadId, DownloadOrchestrator] = {}
        self._orchestrator_threads: dict[DownloadId, threading.Thread] = {}
        self._lock = threading.Lock()

        self._speed_limiter: TokenBucket | None = (
            TokenBucket(float(global_speed_limit_bps)) if global_speed_limit_bps else None
        )

    def start_download(self, download_id: DownloadId) -> bool:
        """Start or resume a download task in a background worker thread."""
        with self._lock:
            if download_id in self._active_orchestrators:
                return False

            download = self.download_repo.get_by_id(download_id)
            if not download:
                return False

            orchestrator = DownloadOrchestrator(
                download=download,
                download_repo=self.download_repo,
                segment_repo=self.segment_repo,
                manifest_storage=self.manifest_storage,
                http_client=self.http_client,
                progress_reporter=self.progress_reporter,
                speed_limiter=self._speed_limiter,
            )

            self._active_orchestrators[download_id] = orchestrator

            thread = threading.Thread(
                target=self._run_orchestrator,
                args=(download_id, orchestrator),
                name=f"PyIDM-Orchestrator-{download_id}",
                daemon=True,
            )
            self._orchestrator_threads[download_id] = thread
            thread.start()
            return True

    def _run_orchestrator(self, download_id: DownloadId, orchestrator: DownloadOrchestrator) -> None:
        try:
            orchestrator.run()
        finally:
            with self._lock:
                self._active_orchestrators.pop(download_id, None)
                self._orchestrator_threads.pop(download_id, None)

    def pause_download(self, download_id: DownloadId) -> bool:
        """Signal an active download orchestrator to pause cooperatively."""
        with self._lock:
            orchestrator = self._active_orchestrators.get(download_id)
            if orchestrator:
                orchestrator.request_pause()
                return True
            return False

    def cancel_download(self, download_id: DownloadId) -> bool:
        """Signal an active download orchestrator to cancel."""
        with self._lock:
            orchestrator = self._active_orchestrators.get(download_id)
            if orchestrator:
                orchestrator.request_cancel()
                return True
            else:
                # If not active, mark directly in database
                dl = self.download_repo.get_by_id(download_id)
                if dl:
                    dl.status = DownloadStatus.CANCELLED
                    self.download_repo.save(dl)
                    return True
            return False

    def get_active_count(self) -> int:
        with self._lock:
            return len(self._active_orchestrators)

    def set_global_speed_limit(self, bps: int | None) -> None:
        """Dynamically update or disable global bandwidth throttling."""
        with self._lock:
            if bps and bps > 0:
                if self._speed_limiter:
                    self._speed_limiter.set_rate(float(bps))
                else:
                    self._speed_limiter = TokenBucket(float(bps))
            else:
                self._speed_limiter = None

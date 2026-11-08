"""Per-download orchestrator coordinating inspection, segmentation, workers, and assembly."""

from __future__ import annotations

import threading
from datetime import datetime

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.enums.strategy import DownloadStrategy
from app.domain.downloads.interfaces.progress_reporter import ProgressReporter
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)
from app.domain.downloads.services.category_classifier import CategoryClassifier
from app.domain.downloads.services.segment_calculator import SegmentCalculator
from app.domain.downloads.value_objects.ids import create_segment_id
from app.engine.assembly.file_assembler import FileAssembler
from app.engine.monitoring.progress_aggregator import ProgressAggregator
from app.engine.monitoring.token_bucket import TokenBucket
from app.engine.retry.retry_coordinator import ErrorClassifier, RetryCoordinator
from app.engine.workers.segment_worker import SegmentWorker
from app.engine.workers.worker_pool import WorkerPool
from app.infrastructure.filesystem.manifest_storage import (
    DownloadManifest,
    JsonManifestStorage,
    SegmentRecord,
)
from app.infrastructure.networking.http_stream_client import HttpStreamClient


class DownloadOrchestrator:
    """Manages the full download lifecycle for an individual Download aggregate."""

    def __init__(
        self,
        download: Download,
        download_repo: DownloadRepository,
        segment_repo: SegmentRepository,
        manifest_storage: JsonManifestStorage,
        http_client: HttpStreamClient,
        progress_reporter: ProgressReporter | None = None,
        speed_limiter: TokenBucket | None = None,
        worker_pool: WorkerPool | None = None,
    ) -> None:
        self.download = download
        self.download_repo = download_repo
        self.segment_repo = segment_repo
        self.manifest_storage = manifest_storage
        self.http_client = http_client
        self.progress_reporter = progress_reporter
        self.speed_limiter = speed_limiter

        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()

        self._worker_pool = worker_pool or WorkerPool(max_workers=download.connection_count)
        self._progress_aggregator = ProgressAggregator(download, progress_reporter)
        self._retry_coordinator = RetryCoordinator(self.cancel_event)
        self._assembler = FileAssembler()

    def request_pause(self) -> None:
        """Signal cooperative pause to all active workers."""
        self.pause_event.set()
        self.download.status = DownloadStatus.PAUSING
        self.download_repo.save(self.download)
        if self.progress_reporter:
            self.progress_reporter.report_status_change(self.download.id, DownloadStatus.PAUSING)

    def request_cancel(self) -> None:
        """Signal cancellation to all active workers."""
        self.cancel_event.set()
        self.download.status = DownloadStatus.CANCELLED
        self.download_repo.save(self.download)
        if self.progress_reporter:
            self.progress_reporter.report_status_change(self.download.id, DownloadStatus.CANCELLED)

    def run(self) -> bool:
        """Execute the download to completion. Returns True if completed."""
        try:
            # 1. Inspect resource if total size is unknown
            if self.download.total_size <= 0:
                self.download.status = DownloadStatus.INSPECTING
                self.download_repo.save(self.download)
                if self.progress_reporter:
                    self.progress_reporter.report_status_change(
                        self.download.id, DownloadStatus.INSPECTING
                    )

                meta = self.http_client.inspect(
                    self.download.url.raw, self.download.custom_headers
                )

                if meta.content_length:
                    self.download.total_size = meta.content_length
                self.download.etag = meta.etag
                self.download.last_modified = meta.last_modified
                self.download.content_type = meta.content_type

                # Auto-categorize
                self.download.category = CategoryClassifier.classify(
                    meta.content_type, self.download.filename
                )

                if meta.accept_ranges and meta.content_length and meta.content_length > 1_000_000:
                    self.download.strategy = DownloadStrategy.SEGMENTED
                else:
                    self.download.strategy = DownloadStrategy.SINGLE_STREAM

            if self.cancel_event.is_set():
                return False

            # 2. Plan or retrieve segments
            segments = self.segment_repo.get_by_download_id(self.download.id)
            temp_dir = self.manifest_storage.get_manifest_path(self.download.id).parent

            if not segments:
                temp_dir.mkdir(parents=True, exist_ok=True)
                if self.download.strategy == DownloadStrategy.SEGMENTED and self.download.total_size > 0:
                    ranges = SegmentCalculator.calculate(
                        self.download.total_size, self.download.connection_count
                    )
                else:
                    ranges = SegmentCalculator.calculate(
                        self.download.total_size, 1
                    )

                segments = []
                for idx, r in enumerate(ranges):
                    part_file = temp_dir / f"segment_{idx:03d}.part"
                    seg = DownloadSegment(
                        id=create_segment_id(),
                        download_id=self.download.id,
                        segment_index=idx,
                        byte_range=r,
                        temp_file_path=part_file,
                    )
                    segments.append(seg)
                self.segment_repo.save_all(segments)

                # Save initial manifest
                manifest = DownloadManifest(
                    download_id=str(self.download.id),
                    total_size=self.download.total_size,
                    strategy=self.download.strategy.value if self.download.strategy else "SINGLE_STREAM",
                    etag=self.download.etag,
                    last_modified=self.download.last_modified,
                    created_at=datetime.utcnow().isoformat(),
                    segments=[
                        SegmentRecord(
                            id=str(s.id),
                            segment_index=s.segment_index,
                            start_byte=s.byte_range.start,
                            end_byte=s.byte_range.end,
                            downloaded_bytes=s.downloaded_bytes,
                            status=s.status.value,
                            temp_file_path=str(s.temp_file_path) if s.temp_file_path else None,
                        )
                        for s in segments
                    ],
                )
                self.manifest_storage.save(manifest)

            # 3. Transition to DOWNLOADING
            self.download.status = DownloadStatus.DOWNLOADING
            self.download.started_at = self.download.started_at or datetime.utcnow()
            self.download_repo.save(self.download)
            if self.progress_reporter:
                self.progress_reporter.report_status_change(
                    self.download.id, DownloadStatus.DOWNLOADING
                )

            # 4. Spawn workers
            workers = [
                SegmentWorker(
                    segment=seg,
                    url=self.download.url.raw,
                    http_client=self.http_client,
                    cancel_event=self.cancel_event,
                    pause_event=self.pause_event,
                    progress_callback=self._progress_aggregator.record_chunk,
                    speed_limiter=self.speed_limiter,
                )
                for seg in segments
                if not seg.is_complete
            ]

            if workers:
                self._worker_pool.execute_workers(workers)
                self.segment_repo.save_all(segments)
                self.download.downloaded_bytes = sum(s.downloaded_bytes for s in segments)
                self.download_repo.save(self.download)

            # Check pause / cancel
            if self.pause_event.is_set():
                self.download.status = DownloadStatus.PAUSED
                self.download_repo.save(self.download)
                self._progress_aggregator.force_emit()
                if self.progress_reporter:
                    self.progress_reporter.report_status_change(
                        self.download.id, DownloadStatus.PAUSED
                    )
                return False

            if self.cancel_event.is_set():
                self.download.status = DownloadStatus.CANCELLED
                self.download_repo.save(self.download)
                if self.progress_reporter:
                    self.progress_reporter.report_status_change(
                        self.download.id, DownloadStatus.CANCELLED
                    )
                return False

            # 5. Verify completeness
            if not all(s.is_complete for s in segments):
                raise RuntimeError("Not all segments completed successfully")

            self.download.status = DownloadStatus.VERIFYING
            self.download_repo.save(self.download)
            if self.progress_reporter:
                self.progress_reporter.report_status_change(
                    self.download.id, DownloadStatus.VERIFYING
                )

            # 6. Assemble file
            self.download.status = DownloadStatus.ASSEMBLING
            self.download_repo.save(self.download)
            if self.progress_reporter:
                self.progress_reporter.report_status_change(
                    self.download.id, DownloadStatus.ASSEMBLING
                )

            self._assembler.assemble(
                segments=segments,
                final_destination=self.download.final_path,
                expected_total_size=self.download.total_size,
            )

            # 7. Mark COMPLETED
            self.download.status = DownloadStatus.COMPLETED
            self.download.completed_at = datetime.utcnow()
            self.download.downloaded_bytes = self.download.total_size
            self.download_repo.save(self.download)
            self._progress_aggregator.force_emit()

            if self.progress_reporter:
                self.progress_reporter.report_status_change(
                    self.download.id, DownloadStatus.COMPLETED
                )

            # Clean up temporary part files and manifest
            for s in segments:
                if s.temp_file_path and s.temp_file_path.exists():
                    s.temp_file_path.unlink()
            self.manifest_storage.delete(self.download.id)

            return True

        except Exception as ex:
            cat = ErrorClassifier.classify(ex)
            self.download.mark_failed(str(ex), cat)
            self.download_repo.save(self.download)
            if self.progress_reporter:
                self.progress_reporter.report_error(self.download.id, str(ex))
            return False

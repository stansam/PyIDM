"""Progress aggregator collecting segment progress and throttling notifications."""

from __future__ import annotations

import threading
import time

from app.domain.downloads.entities.download import Download
from app.domain.downloads.interfaces.progress_reporter import ProgressReporter
from app.domain.downloads.value_objects.ids import SegmentId
from app.engine.monitoring.speed_meter import RollingSpeedMeter
from app.shared.constants import PROGRESS_EMIT_INTERVAL_SEC


class ProgressAggregator:
    """Aggregates raw chunk writes across segment workers and throttles UI updates."""

    def __init__(
        self,
        download: Download,
        reporter: ProgressReporter | None = None,
        emit_interval_sec: float = PROGRESS_EMIT_INTERVAL_SEC,
    ) -> None:
        self.download = download
        self.reporter = reporter
        self.emit_interval = emit_interval_sec
        self.speed_meter = RollingSpeedMeter()
        self.last_emit = time.monotonic()
        self._lock = threading.Lock()

    def record_chunk(self, segment_id: SegmentId, bytes_written: int) -> None:
        """Called by SegmentWorker when a chunk is written to disk."""
        speed = self.speed_meter.update(bytes_written)

        with self._lock:
            self.download.downloaded_bytes += bytes_written
            now = time.monotonic()

            if now - self.last_emit >= self.emit_interval:
                self.last_emit = now
                if self.reporter:
                    progress = self.download.to_progress(speed.bytes_per_second)
                    self.reporter.report_progress(self.download.id, progress)

    def force_emit(self) -> None:
        """Bypass throttle and report final or paused progress state."""
        with self._lock:
            if self.reporter:
                progress = self.download.to_progress(0.0)
                self.reporter.report_progress(self.download.id, progress)


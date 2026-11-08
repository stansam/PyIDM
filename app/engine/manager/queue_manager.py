"""Download queue entity and queue manager controlling download progression."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.interfaces.repositories import DownloadRepository
from app.domain.downloads.value_objects.ids import DownloadId, QueueId
from app.engine.manager.download_manager import DownloadManager
from app.shared.types import Priority


class QueueStatus(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


@dataclass
class DownloadQueue:
    """Represents an ordered collection of downloads with concurrency constraints."""

    id: QueueId
    name: str
    status: QueueStatus = QueueStatus.IDLE
    max_concurrent: int = 2
    priority: Priority = Priority.NORMAL
    download_ids: list[DownloadId] = field(default_factory=list)

    def add_download(self, download_id: DownloadId) -> None:
        if download_id not in self.download_ids:
            self.download_ids.append(download_id)

    def remove_download(self, download_id: DownloadId) -> None:
        if download_id in self.download_ids:
            self.download_ids.remove(download_id)


class QueueManager:
    """Manages queue progression, concurrent slot limits, and queue priorities."""

    def __init__(
        self,
        download_manager: DownloadManager,
        download_repo: DownloadRepository,
        max_global_concurrent: int = 3,
    ) -> None:
        self.download_manager = download_manager
        self.download_repo = download_repo
        self.max_global_concurrent = max_global_concurrent

        self._queues: dict[QueueId, DownloadQueue] = {}
        self._lock = threading.Lock()

    def register_queue(self, queue: DownloadQueue) -> None:
        with self._lock:
            self._queues[queue.id] = queue

    def get_queue(self, queue_id: QueueId) -> DownloadQueue | None:
        with self._lock:
            return self._queues.get(queue_id)

    def start_queue(self, queue_id: QueueId) -> None:
        with self._lock:
            q = self._queues.get(queue_id)
            if q:
                q.status = QueueStatus.RUNNING

    def pause_queue(self, queue_id: QueueId) -> None:
        with self._lock:
            q = self._queues.get(queue_id)
            if q:
                q.status = QueueStatus.PAUSED
                for dl_id in q.download_ids:
                    self.download_manager.pause_download(dl_id)

    def tick(self) -> int:
        """Evaluate running queues and dispatch downloads into open concurrency slots."""
        with self._lock:
            active_count = self.download_manager.get_active_count()
            available_global_slots = max(0, self.max_global_concurrent - active_count)
            if available_global_slots <= 0:
                return 0

            dispatched = 0
            # Sort queues by priority descending
            running_queues = sorted(
                [q for q in self._queues.values() if q.status == QueueStatus.RUNNING],
                key=lambda q: int(q.priority),
                reverse=True,
            )

            for q in running_queues:
                for dl_id in list(q.download_ids):
                    if dispatched >= available_global_slots:
                        break

                    dl = self.download_repo.get_by_id(dl_id)
                    if dl and dl.status in (DownloadStatus.PENDING, DownloadStatus.QUEUED, DownloadStatus.PAUSED):
                        if self.download_manager.start_download(dl_id):
                            dispatched += 1

            return dispatched

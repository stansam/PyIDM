"""Worker pool executing multi-segment downloads concurrently via ThreadPoolExecutor."""

from __future__ import annotations

import concurrent.futures

from app.engine.workers.segment_worker import SegmentWorker


class WorkerPool:
    """Manages execution and lifecycle of SegmentWorkers across a ThreadPoolExecutor."""

    def __init__(self, max_workers: int = 16) -> None:
        self._max_workers = max_workers
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="PyIDM-Worker",
        )

    def execute_workers(self, workers: list[SegmentWorker]) -> list[bool]:
        """Submit all workers and wait for their completion or cooperative stop."""
        futures = [self._executor.submit(w.run) for w in workers]
        results: list[bool] = []
        for f in futures:
            try:
                results.append(f.result())
            except Exception:
                results.append(False)
        return results

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown worker pool executor."""
        self._executor.shutdown(wait=wait, cancel_futures=True)


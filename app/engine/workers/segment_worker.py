"""Single segment worker executing streaming writes for an assigned byte range."""

from __future__ import annotations

import threading
from collections.abc import Callable

from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.value_objects.ids import SegmentId
from app.engine.monitoring.token_bucket import TokenBucket
from app.infrastructure.networking.http_stream_client import HttpStreamClient
from app.shared.constants import DEFAULT_CHUNK_SIZE_BYTES


class SegmentWorker:
    """Worker task responsible for downloading one byte-range chunk to disk."""

    def __init__(
        self,
        segment: DownloadSegment,
        url: str,
        http_client: HttpStreamClient,
        cancel_event: threading.Event,
        pause_event: threading.Event,
        progress_callback: Callable[[SegmentId, int], None],
        speed_limiter: TokenBucket | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES,
    ) -> None:
        self.segment = segment
        self.url = url
        self.http_client = http_client
        self.cancel_event = cancel_event
        self.pause_event = pause_event
        self.progress_callback = progress_callback
        self.speed_limiter = speed_limiter
        self.chunk_size = chunk_size

    def run(self) -> bool:
        """Download remaining bytes for the assigned range. Returns True if completed."""
        if self.segment.is_complete:
            return True

        assert self.segment.temp_file_path is not None
        self.segment.temp_file_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "r+b" if self.segment.temp_file_path.exists() and self.segment.downloaded_bytes > 0 else "wb"
        start_offset = self.segment.current_offset
        end_offset = self.segment.byte_range.end

        if start_offset > end_offset:
            self.segment.mark_completed()
            return True

        with open(self.segment.temp_file_path, mode) as f:
            if mode == "r+b":
                f.seek(self.segment.downloaded_bytes)

            stream = self.http_client.stream_range(
                url=self.url,
                start_byte=start_offset,
                end_byte=end_offset,
                chunk_size=self.chunk_size,
            )

            for chunk in stream:
                if self.cancel_event.is_set():
                    return False

                if self.pause_event.is_set():
                    f.flush()
                    return False

                if self.speed_limiter:
                    self.speed_limiter.consume(len(chunk))

                f.write(chunk)
                chunk_len = len(chunk)
                self.segment.record_progress(chunk_len)
                self.progress_callback(self.segment.id, chunk_len)

            f.flush()

        return self.segment.is_complete


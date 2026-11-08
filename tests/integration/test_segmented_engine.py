"""Integration tests for multi-segment parallel downloading and assembly."""

import threading
from pathlib import Path

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.strategy import DownloadStrategy
from app.domain.downloads.services.segment_calculator import SegmentCalculator
from app.domain.downloads.value_objects.ids import (
    create_download_id,
    create_segment_id,
)
from app.domain.downloads.value_objects.url import DownloadUrl
from app.engine.assembly.file_assembler import FileAssembler
from app.engine.workers.segment_worker import SegmentWorker
from app.engine.workers.worker_pool import WorkerPool
from app.infrastructure.networking.http_stream_client import HttpStreamClient
from tests.fixtures.mock_http_server import MockHttpHandler, MockHttpServer


def test_segmented_download_and_assembly(tmp_path: Path) -> None:
    server = MockHttpServer()
    server.start()
    try:
        http_client = HttpStreamClient()
        meta = http_client.inspect(server.url)
        assert meta.content_length is not None

        dl_id = create_download_id()
        download = Download(
            id=dl_id,
            url=DownloadUrl.parse(server.url),
            destination_directory=tmp_path,
            filename="assembled_output.bin",
            total_size=meta.content_length,
            strategy=DownloadStrategy.SEGMENTED,
        )

        # 4 segments
        ranges = SegmentCalculator.calculate(
            total_size=meta.content_length, connection_count=4, min_segment_bytes=100_000
        )
        assert len(ranges) == 4

        temp_dir = tmp_path / ".pyidm_temp" / str(dl_id)
        temp_dir.mkdir(parents=True, exist_ok=True)

        segments: list[DownloadSegment] = []
        for i, r in enumerate(ranges):
            part_path = temp_dir / f"segment_{i:03d}.part"
            seg = DownloadSegment(
                id=create_segment_id(),
                download_id=dl_id,
                segment_index=i,
                byte_range=r,
                temp_file_path=part_path,
            )
            segments.append(seg)

        cancel_ev = threading.Event()
        pause_ev = threading.Event()

        workers: list[SegmentWorker] = []
        for seg in segments:
            w = SegmentWorker(
                segment=seg,
                url=server.url,
                http_client=http_client,
                cancel_event=cancel_ev,
                pause_event=pause_ev,
                progress_callback=lambda seg_id, b: None,
            )
            workers.append(w)

        # Execute parallel workers
        pool = WorkerPool(max_workers=4)
        results = pool.execute_workers(workers)
        pool.shutdown()

        assert all(results)
        assert all(s.is_complete for s in segments)

        # Assemble file
        assembler = FileAssembler()
        final_file = assembler.assemble(
            segments=segments,
            final_destination=download.final_path,
            expected_total_size=meta.content_length,
        )

        assert final_file.exists()
        assert final_file.stat().st_size == meta.content_length

        with open(final_file, "rb") as f:
            assembled_bytes = f.read()
        assert assembled_bytes == MockHttpHandler.payload

        http_client.close()
    finally:
        server.stop()


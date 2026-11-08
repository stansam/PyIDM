"""Integration tests for DownloadOrchestrator, RecoveryManager, and QueueManager."""

import threading
from pathlib import Path

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import (
    create_download_id,
    create_queue_id,
)
from app.domain.downloads.value_objects.url import DownloadUrl
from app.engine.downloader.orchestrator import DownloadOrchestrator
from app.engine.manager.download_manager import DownloadManager
from app.engine.manager.queue_manager import DownloadQueue, QueueManager
from app.engine.recovery.recovery_manager import RecoveryManager
from app.infrastructure.filesystem.manifest_storage import JsonManifestStorage
from app.infrastructure.networking.http_stream_client import HttpStreamClient
from app.infrastructure.persistence.database import (
    create_session_factory,
    create_sqlite_engine,
    init_database,
)
from app.infrastructure.persistence.repositories import (
    SqlDownloadRepository,
    SqlSegmentRepository,
)
from tests.fixtures.mock_http_server import MockHttpServer


def test_orchestrator_pause_and_recovery(tmp_path: Path) -> None:
    server = MockHttpServer()
    server.start()
    try:
        db_path = tmp_path / "test.db"
        engine = create_sqlite_engine(db_path)
        init_database(engine)
        session_factory = create_session_factory(engine)

        dl_repo = SqlDownloadRepository(session_factory)
        seg_repo = SqlSegmentRepository(session_factory)
        manifest_storage = JsonManifestStorage(tmp_path / ".pyidm_temp")
        http_client = HttpStreamClient()

        dl_id = create_download_id()
        download = Download(
            id=dl_id,
            url=DownloadUrl.parse(server.url),
            destination_directory=tmp_path,
            filename="pause_test.bin",
            connection_count=4,
        )
        dl_repo.save(download)

        orchestrator = DownloadOrchestrator(
            download=download,
            download_repo=dl_repo,
            segment_repo=seg_repo,
            manifest_storage=manifest_storage,
            http_client=http_client,
        )

        # Trigger pause immediately after start
        t = threading.Thread(target=orchestrator.run)
        t.start()
        orchestrator.request_pause()
        t.join(timeout=5.0)

        assert download.status in (DownloadStatus.PAUSED, DownloadStatus.PAUSING)

        # Test Recovery Manager
        recovery = RecoveryManager(dl_repo, seg_repo, manifest_storage)
        candidates = recovery.scan_and_reconcile()
        assert len(candidates) == 1
        assert candidates[0].download.id == dl_id
        assert candidates[0].is_recoverable is True

        http_client.close()
    finally:
        server.stop()


def test_queue_manager_progression(tmp_path: Path) -> None:
    db_path = tmp_path / "queue_test.db"
    engine = create_sqlite_engine(db_path)
    init_database(engine)
    session_factory = create_session_factory(engine)

    dl_repo = SqlDownloadRepository(session_factory)
    seg_repo = SqlSegmentRepository(session_factory)
    manifest_storage = JsonManifestStorage(tmp_path / ".pyidm_temp")
    http_client = HttpStreamClient()

    dl_mgr = DownloadManager(
        download_repo=dl_repo,
        segment_repo=seg_repo,
        manifest_storage=manifest_storage,
        http_client=http_client,
        max_active_downloads=2,
    )

    queue_mgr = QueueManager(dl_mgr, dl_repo, max_global_concurrent=2)
    q_id = create_queue_id()
    queue = DownloadQueue(id=q_id, name="Default")

    dl_id1 = create_download_id()
    dl1 = Download(
        id=dl_id1,
        url=DownloadUrl.parse("https://example.com/item1.zip"),
        destination_directory=tmp_path,
        filename="item1.zip",
    )
    dl_repo.save(dl1)
    queue.add_download(dl_id1)

    queue_mgr.register_queue(queue)
    queue_mgr.start_queue(q_id)

    # Queue should detect pending and attempt dispatch
    dispatched = queue_mgr.tick()
    assert dispatched == 1
    assert dl_mgr.get_active_count() <= 1

    http_client.close()

"""Dependency injection container wiring all architectural layers."""

from __future__ import annotations

from app.application.signals.download_signals import DownloadSignalEmitter
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)
from app.engine.manager.download_manager import DownloadManager
from app.engine.manager.queue_manager import QueueManager
from app.infrastructure.configuration.app_settings import AppSettings
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


class Container:
    """Explicit dependency injection container."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings: AppSettings = settings or AppSettings()

        # Database & Repositories
        self.engine = create_sqlite_engine(self.settings.db_path)
        init_database(self.engine)
        self.session_factory = create_session_factory(self.engine)

        self.download_repo: DownloadRepository = SqlDownloadRepository(self.session_factory)
        self.segment_repo: SegmentRepository = SqlSegmentRepository(self.session_factory)
        self.manifest_storage = JsonManifestStorage(self.settings.temp_dir)

        # Networking & Signal Adapters
        self.http_client = HttpStreamClient()
        self.signal_emitter = DownloadSignalEmitter()

        # Engine
        self.download_manager = DownloadManager(
            download_repo=self.download_repo,
            segment_repo=self.segment_repo,
            manifest_storage=self.manifest_storage,
            http_client=self.http_client,
            progress_reporter=self.signal_emitter,
            max_active_downloads=self.settings.max_concurrent_downloads,
            global_speed_limit_bps=self.settings.global_speed_limit_bps,
        )

        self.queue_manager = QueueManager(
            download_manager=self.download_manager,
            download_repo=self.download_repo,
            max_global_concurrent=self.settings.max_concurrent_downloads,
        )


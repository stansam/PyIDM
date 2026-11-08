"""Desktop application entry point and PySide6 event loop bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.application.container import Container
from app.engine.recovery.recovery_manager import RecoveryManager
from app.infrastructure.configuration.app_settings import AppSettings
from app.presentation.themes.theme_manager import ThemeManager
from app.presentation.windows.main_window import MainWindow


def main() -> int:
    """Initialize application, run crash recovery, apply theme, and start Qt loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("PyIDM")
    app.setOrganizationName("PyIDM")

    settings = AppSettings()
    container = Container(settings)

    # 1. Startup crash recovery scan
    recovery_mgr = RecoveryManager(
        download_repo=container.download_repo,
        segment_repo=container.segment_repo,
        manifest_storage=container.manifest_storage,
    )
    recovery_mgr.scan_and_reconcile()

    # 2. Apply User Configured Theme (Dark / Light / System)
    ThemeManager.apply_theme(app, settings.theme)

    # 3. Create and Show MainWindow
    window = MainWindow(container)
    window.show()

    # 4. Start Local Browser API Server (127.0.0.1:8743)
    from app.infrastructure.browser.server import LocalApiServer
    api_server = LocalApiServer(container)
    api_server.start()

    ret = app.exec()
    api_server.stop()
    return ret


if __name__ == "__main__":
    sys.exit(main())

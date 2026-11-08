"""Desktop application entry point and PySide6 event loop bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.application.container import Container
from app.engine.recovery.recovery_manager import RecoveryManager
from app.infrastructure.configuration.app_settings import AppSettings
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

    # 2. Apply Dark Theme QSS
    theme_path = Path(__file__).parent / "presentation" / "themes" / "dark.qss"
    if theme_path.exists():
        with open(theme_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # 3. Create and Show MainWindow
    window = MainWindow(container)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

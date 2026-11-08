"""CLI launcher for PyIDM Native Messaging Host."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path when invoked via host.bat
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.application.container import Container
from app.infrastructure.browser.native_host import NativeMessagingHost
from app.infrastructure.configuration.app_settings import AppSettings


def main() -> int:
    """Initialize Container and enter native messaging loop."""
    settings = AppSettings()
    container = Container(settings)
    host = NativeMessagingHost(container)
    host.run_loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

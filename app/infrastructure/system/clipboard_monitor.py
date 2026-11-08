"""System clipboard monitor observing the clipboard for downloadable URLs."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QClipboard, QGuiApplication

from app.domain.downloads.value_objects.url import DownloadUrl


class ClipboardMonitor(QObject):
    """Monitors OS clipboard for HTTP/HTTPS URLs and invokes a callback if detected."""

    def __init__(self, on_url_detected: Callable[[str], None], enabled: bool = True) -> None:
        super().__init__()
        self.on_url_detected = on_url_detected
        self.enabled = enabled
        self._last_text = ""
        self._clipboard: QClipboard | None = None

        if self.enabled:
            self.start()

    def start(self) -> None:
        """Attach listener to the Qt system clipboard."""
        app = QGuiApplication.instance()
        if app is not None:
            self._clipboard = QGuiApplication.clipboard()
            if self._clipboard is not None:
                self._clipboard.dataChanged.connect(self._on_clipboard_changed)

    def stop(self) -> None:
        """Detach listener."""
        if self._clipboard is not None:
            try:
                self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass
            self._clipboard = None

    def _on_clipboard_changed(self) -> None:
        if not self.enabled or self._clipboard is None:
            return

        text = self._clipboard.text().strip()
        if not text or text == self._last_text:
            return

        self._last_text = text

        try:
            url = DownloadUrl.parse(text)
            # Only trigger callback for valid HTTP/HTTPS URLs with common extensions or non-empty paths
            if url.path and ("." in url.path or len(url.path) > 1):
                self.on_url_detected(url.raw)
        except Exception:
            # Not a valid downloadable URL, ignore silently
            pass

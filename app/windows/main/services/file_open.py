"""Operating system file and clipboard integration service."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox, QWidget


class FileOpenService:
    """Provides platform-agnostic file, directory, and clipboard operations."""

    @staticmethod
    def open_folder(parent: QWidget | None, path: Path) -> None:
        """Open containing directory in native desktop file explorer."""
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        else:
            QMessageBox.warning(parent, "Directory Not Found", f"Cannot find directory: {path}")

    @staticmethod
    def open_file(parent: QWidget | None, file_path: Path) -> None:
        """Open file using default registered operating system application."""
        if file_path.exists():
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
        else:
            QMessageBox.warning(parent, "File Not Found", f"Cannot find file: {file_path}")

    @staticmethod
    def copy_link(url: str) -> None:
        """Copy download URL string to system clipboard."""
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(url)


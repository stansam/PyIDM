"""Download Details modal dialog presenting diagnostics and segment information."""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.value_objects.file_size import FileSize


class DownloadDetailsDialog(QDialog):
    """Dialog showing deep diagnostic details and segment breakdown for a download."""

    def __init__(
        self,
        download: Download,
        segments: list[DownloadSegment] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.download = download
        self.segments = segments or []
        self.setWindowTitle(f"Download Details — {download.filename}")
        self.resize(600, 420)

        main_layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # Tab 1: General Info
        general_widget = QWidget()
        form = QFormLayout(general_widget)
        form.setContentsMargins(12, 12, 12, 12)

        url_edit = QLineEdit(download.url.raw)
        url_edit.setReadOnly(True)
        form.addRow("URL:", url_edit)

        name_edit = QLineEdit(download.filename)
        name_edit.setReadOnly(True)
        form.addRow("File Name:", name_edit)

        dest_edit = QLineEdit(str(download.destination_directory))
        dest_edit.setReadOnly(True)
        form.addRow("Destination:", dest_edit)

        size_str = FileSize(download.total_size).formatted if download.total_size > 0 else "Unknown"
        form.addRow("Total Size:", QLabel(size_str))

        downloaded_str = FileSize(download.downloaded_bytes).formatted
        form.addRow("Downloaded:", QLabel(downloaded_str))

        form.addRow("Status:", QLabel(download.status.value))
        form.addRow("Category:", QLabel(download.category.value))
        form.addRow("Connections:", QLabel(str(download.connection_count)))

        if download.etag:
            form.addRow("ETag:", QLabel(download.etag))
        if download.last_modified:
            form.addRow("Last-Modified:", QLabel(download.last_modified))

        tabs.addTab(general_widget, "General")

        # Tab 2: Segments Information
        segments_widget = QWidget()
        seg_layout = QVBoxLayout(segments_widget)
        seg_text = QTextEdit()
        seg_text.setReadOnly(True)

        if self.segments:
            lines: list[str] = []
            for seg in sorted(self.segments, key=lambda s: s.segment_index):
                pct = (
                    (seg.downloaded_bytes / seg.byte_range.length * 100.0)
                    if seg.byte_range.length > 0
                    else 0.0
                )
                lines.append(
                    f"Segment #{seg.segment_index:02d}: "
                    f"Range {seg.byte_range.start:,} - {seg.byte_range.end:,} "
                    f"({FileSize(seg.byte_range.length).formatted}) | "
                    f"Status: {seg.status.value} | "
                    f"Downloaded: {FileSize(seg.downloaded_bytes).formatted} ({pct:.1f}%)"
                )
            seg_text.setPlainText("\n".join(lines))
        else:
            seg_text.setPlainText("No segment records available for this task.")

        seg_layout.addWidget(seg_text)
        tabs.addTab(segments_widget, f"Segments ({len(self.segments)})")

        # Tab 3: Diagnostics / Error logs
        diag_widget = QWidget()
        diag_layout = QVBoxLayout(diag_widget)
        diag_text = QTextEdit()
        diag_text.setReadOnly(True)
        diag_info: list[str] = [
            f"Download ID: {self.download.id}",
            f"Created At: {self.download.created_at.isoformat()}",
            f"Started At: {self.download.started_at.isoformat() if self.download.started_at else 'N/A'}",
            f"Completed At: {self.download.completed_at.isoformat() if self.download.completed_at else 'N/A'}",
        ]
        if self.download.error_message:
            diag_info.append(f"\n--- Error Details ---\nCategory: {self.download.error_category}\nMessage: {self.download.error_message}")

        diag_text.setPlainText("\n".join(diag_info))
        diag_layout.addWidget(diag_text)
        tabs.addTab(diag_widget, "Diagnostics")

        main_layout.addWidget(tabs)

        # Action Buttons
        btn_layout = QHBoxLayout()
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self._open_folder)
        btn_layout.addWidget(open_folder_btn)

        if download.final_path.exists():
            open_file_btn = QPushButton("Open File")
            open_file_btn.clicked.connect(self._open_file)
            btn_layout.addWidget(open_file_btn)

        btn_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        btn_layout.addWidget(button_box)

        main_layout.addLayout(btn_layout)

    def _open_folder(self) -> None:
        path = self.download.destination_directory
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        else:
            QMessageBox.warning(self, "Directory Not Found", f"Cannot find directory: {path}")

    def _open_file(self) -> None:
        file_path = self.download.final_path
        if file_path.exists():
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
        else:
            QMessageBox.warning(self, "File Not Found", f"Cannot find file: {file_path}")


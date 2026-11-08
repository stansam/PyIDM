"""Main application window for PyIDM."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.presentation.dialogs.add_download_dialog import AddDownloadDialog
from app.presentation.models.download_table_model import DownloadTableModel


class MainWindow(QMainWindow):
    """Main application window presenting the download dashboard and controls."""

    def __init__(self, container: Container) -> None:
        super().__init__()
        self.container = container
        self.setWindowTitle("PyIDM — Python Internet Download Manager")
        self.resize(980, 580)

        # Central Widget & Layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        # Table Model & View
        self.table_model = DownloadTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table_view)

        self.setCentralWidget(central)

        # ToolBar & Actions
        self._setup_toolbar()

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")

        # Wire Signals from Engine Adapter
        self.container.signal_emitter.progress_updated.connect(
            self.table_model.update_progress
        )
        self.container.signal_emitter.status_changed.connect(
            self.table_model.update_status
        )

        self._refresh_downloads()

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Controls")
        self.addToolBar(toolbar)

        add_action = QAction("➕ Add URL", self)
        add_action.triggered.connect(self._on_add_download)
        toolbar.addAction(add_action)

        resume_action = QAction("▶ Resume", self)
        resume_action.triggered.connect(self._on_resume_selected)
        toolbar.addAction(resume_action)

        pause_action = QAction("⏸ Pause", self)
        pause_action.triggered.connect(self._on_pause_selected)
        toolbar.addAction(pause_action)

        cancel_action = QAction("⏹ Cancel", self)
        cancel_action.triggered.connect(self._on_cancel_selected)
        toolbar.addAction(cancel_action)

        delete_action = QAction("🗑 Delete", self)
        delete_action.triggered.connect(self._on_delete_selected)
        toolbar.addAction(delete_action)

    def _refresh_downloads(self) -> None:
        all_downloads = self.container.download_repo.get_all()
        self.table_model.set_downloads(all_downloads)

    def _on_add_download(self) -> None:
        dlg = AddDownloadDialog(self.container.settings.download_dir, self)
        if dlg.exec():
            url_str, filename, dest_dir, conns = dlg.get_result()
            dl = Download(
                id=create_download_id(),
                url=DownloadUrl.parse(url_str),
                destination_directory=dest_dir,
                filename=filename,
                connection_count=conns,
            )
            self.container.download_repo.save(dl)
            self._refresh_downloads()
            self.container.download_manager.start_download(dl.id)

    def _get_selected_download(self) -> Download | None:
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            return None
        return self.table_model.get_download(selected[0].row())

    def _on_resume_selected(self) -> None:
        dl = self._get_selected_download()
        if dl:
            self.container.download_manager.start_download(dl.id)

    def _on_pause_selected(self) -> None:
        dl = self._get_selected_download()
        if dl:
            self.container.download_manager.pause_download(dl.id)

    def _on_cancel_selected(self) -> None:
        dl = self._get_selected_download()
        if dl:
            self.container.download_manager.cancel_download(dl.id)

    def _on_delete_selected(self) -> None:
        dl = self._get_selected_download()
        if dl:
            self.container.download_manager.cancel_download(dl.id)
            self.container.download_repo.delete(dl.id)
            self._refresh_downloads()

    def _show_context_menu(self, pos: QPoint) -> None:
        dl = self._get_selected_download()
        if not dl:
            return

        menu = QMenu(self)
        if dl.status in (DownloadStatus.PAUSED, DownloadStatus.PENDING, DownloadStatus.FAILED):
            menu.addAction("Resume", self._on_resume_selected)
        if dl.status == DownloadStatus.DOWNLOADING:
            menu.addAction("Pause", self._on_pause_selected)

        menu.addAction("Open Containing Folder", lambda: self._open_folder(dl.destination_directory))
        if dl.status == DownloadStatus.COMPLETED:
            menu.addAction("Open File", lambda: self._open_file(dl.final_path))

        menu.addSeparator()
        menu.addAction("Delete Record", self._on_delete_selected)
        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _open_folder(self, path: Path) -> None:
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])

    def _open_file(self, file_path: Path) -> None:
        if file_path.exists():
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
        else:
            QMessageBox.warning(self, "File Not Found", f"Cannot find: {file_path}")

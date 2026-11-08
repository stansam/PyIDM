"""Action handlers for download lifecycle and application dialogs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from app.domain.downloads.entities.download import Download
from app.domain.downloads.interfaces.repositories import SegmentRepository
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.configuration.app_settings import AppSettings
from app.presentation.dialogs.add_download_dialog import AddDownloadDialog
from app.presentation.dialogs.download_details_dialog import DownloadDetailsDialog
from app.presentation.dialogs.help_dialog import HelpDialog
from app.presentation.dialogs.settings_dialog import SettingsDialog


class DownloadActionsController:
    """Coordinates dialog interactions and download creation/deletion operations."""

    @staticmethod
    def prompt_add_download(
        parent: QWidget,
        default_dir: Path,
        initial_url: str | None = None,
    ) -> Download | None:
        """Display AddDownloadDialog and return created Download entity or None if cancelled."""
        dlg = AddDownloadDialog(default_dir, parent)
        if initial_url:
            dlg.url_edit.setText(initial_url)
        if dlg.exec():
            url_str, filename, dest_dir, conns = dlg.get_result()
            return Download(
                id=create_download_id(),
                url=DownloadUrl.parse(url_str),
                destination_directory=dest_dir,
                filename=filename,
                connection_count=conns,
            )
        return None

    @staticmethod
    def prompt_confirm_delete(parent: QWidget, filename: str) -> bool:
        """Display delete confirmation box and return True if user confirmed."""
        reply = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete '{filename}' from PyIDM?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    @staticmethod
    def show_details(
        parent: QWidget,
        download: Download,
        segment_repo: SegmentRepository,
    ) -> None:
        """Display detailed segmented progress and metadata for download entity."""
        segments = segment_repo.get_by_download_id(download.id)
        dlg = DownloadDetailsDialog(download, segments, parent)
        dlg.exec()

    @staticmethod
    def show_settings(parent: QWidget, settings: AppSettings) -> bool:
        """Display settings configuration dialog and return True if accepted."""
        dlg = SettingsDialog(settings, parent)
        return dlg.exec() == QDialog.DialogCode.Accepted

    @staticmethod
    def show_help(parent: QWidget) -> None:
        """Display help and shortcut information dialog."""
        dlg = HelpDialog(parent)
        dlg.exec()


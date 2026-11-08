"""Context menu builder for download table view."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QWidget

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.download_status import DownloadStatus
from app.presentation.icons import (
    IconColor,
    IconManager,
    IconName,
    IconSize,
)


class TableContextMenuController:
    """Builds and executes context menus for download items."""

    @staticmethod
    def show_context_menu(
        parent: QWidget,
        pos: QPoint,
        download: Download | None,
        icons: IconManager,
        on_resume: Callable[[], None],
        on_pause: Callable[[], None],
        on_cancel: Callable[[], None],
        on_open_folder: Callable[[Path], None],
        on_open_file: Callable[[Path], None],
        on_copy_link: Callable[[str], None],
        on_select_completed: Callable[[], None],
        on_select_failed: Callable[[], None],
        on_select_all: Callable[[], None],
        on_show_details: Callable[[], None],
        on_delete: Callable[[], None],
    ) -> None:
        """Construct context menu based on download status and exec at screen position."""
        if download is None:
            return

        menu = QMenu(parent)

        if download.status in (DownloadStatus.PAUSED, DownloadStatus.PENDING, DownloadStatus.FAILED):
            menu.addAction(
                icons.get(IconName.RESUME, IconColor.PRIMARY, IconSize.COMPACT),
                "Resume",
                on_resume,
            )
        if download.status == DownloadStatus.DOWNLOADING:
            menu.addAction(
                icons.get(IconName.PAUSE, IconColor.WARNING, IconSize.COMPACT),
                "Pause",
                on_pause,
            )

        menu.addAction(
            icons.get(IconName.STOP, IconColor.ERROR, IconSize.COMPACT),
            "Stop / Cancel",
            on_cancel,
        )
        menu.addSeparator()

        menu.addAction(
            icons.get(IconName.FOLDER_OPEN, IconColor.SECONDARY, IconSize.COMPACT),
            "Open Containing Folder",
            lambda: on_open_folder(download.destination_directory),
        )
        if download.status == DownloadStatus.COMPLETED:
            menu.addAction(
                icons.get(IconName.FILE, IconColor.SECONDARY, IconSize.COMPACT),
                "Open File",
                lambda: on_open_file(download.final_path),
            )

        menu.addAction(
            icons.get(IconName.LINK, IconColor.SECONDARY, IconSize.COMPACT),
            "Copy Download Link",
            lambda: on_copy_link(download.url.raw),
        )
        menu.addSeparator()

        menu.addAction(
            icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.COMPACT),
            "Select Completed Tasks",
            on_select_completed,
        )
        menu.addAction(
            icons.get(IconName.CHECK_FAILED, IconColor.ERROR, IconSize.COMPACT),
            "Select Failed Tasks",
            on_select_failed,
        )
        menu.addAction(
            icons.get(IconName.SELECT_ALL, IconColor.SECONDARY, IconSize.COMPACT),
            "Select All",
            on_select_all,
        )
        menu.addSeparator()

        menu.addAction(
            icons.get(IconName.INFO, IconColor.PRIMARY, IconSize.COMPACT),
            "View Details...",
            on_show_details,
        )
        menu.addAction(
            icons.get(IconName.DELETE, IconColor.ERROR, IconSize.COMPACT),
            "Delete Record",
            on_delete,
        )

        menu.exec(pos)


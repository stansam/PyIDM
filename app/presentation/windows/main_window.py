"""Main application window for PyIDM providing Dual-Mode desktop interface with centralized icons."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.system.clipboard_monitor import ClipboardMonitor
from app.presentation.delegates.segmented_progress_delegate import (
    SegmentedProgressBarDelegate,
)
from app.presentation.dialogs.add_download_dialog import AddDownloadDialog
from app.presentation.dialogs.download_details_dialog import DownloadDetailsDialog
from app.presentation.dialogs.help_dialog import HelpDialog
from app.presentation.dialogs.settings_dialog import SettingsDialog
from app.presentation.icons import (
    IconColor,
    IconName,
    IconSize,
    get_icon_manager,
)
from app.presentation.models.download_table_model import DownloadTableModel


class MainWindow(QMainWindow):
    """Main application window presenting the download dashboard and dual-mode controls."""

    def __init__(self, container: Container) -> None:
        super().__init__()
        self.container = container
        self.icons = get_icon_manager()

        self.setWindowTitle("PyIDM — Python Internet Download Manager")
        self.setWindowIcon(self.icons.get(IconName.DOWNLOAD, IconColor.PRIMARY))
        self.resize(1080, 640)

        self._is_compact_mode: bool = False
        self._current_filter: str = "ALL"
        self._search_query: str = ""

        # Central Layout
        self._central_widget = QWidget()
        self._main_layout = QVBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setCentralWidget(self._central_widget)

        # Download Table Model & View
        self.table_model = DownloadTableModel(icons=self.icons)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)
        self.table_view.doubleClicked.connect(self._on_table_double_clicked)

        # Install custom segmented progress bar delegate on column 2 (Progress)
        self.progress_delegate = SegmentedProgressBarDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(2, self.progress_delegate)

        # Setup Header, Sidebar, and Body Splitter
        self._setup_header_toolbar()
        self._setup_body()
        self._setup_footer_statusbar()

        # Wire Signals from Engine Adapter
        self.container.signal_emitter.progress_updated.connect(self._on_progress_updated)
        self.container.signal_emitter.status_changed.connect(self._on_status_changed)

        # Setup Clipboard Monitor
        if self.container.settings.enable_clipboard_monitor:
            self._clipboard_monitor: ClipboardMonitor | None = ClipboardMonitor(
                on_url_detected=self._on_clipboard_url_detected,
                enabled=True,
            )
        else:
            self._clipboard_monitor = None

        self._refresh_downloads()

    def _setup_header_toolbar(self) -> None:
        """Create header toolbar with centralized icons matching page.jfif and compact.jfif."""
        self.toolbar = QToolBar("Main Controls")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # Profile Selector
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Default Profile", "Work", "High-Priority"])
        self.profile_combo.setToolTip("Active download connection profile")
        self.toolbar.addWidget(self.profile_combo)
        self.toolbar.addSeparator()

        # Primary Action Buttons with QtAwesome MDI icons
        self.add_action = QAction(
            self.icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.TOOLBAR),
            "New",
            self,
        )
        self.add_action.setToolTip("Add a new download URL")
        self.add_action.triggered.connect(self._on_add_download)
        self.toolbar.addAction(self.add_action)

        self.resume_action = QAction(
            self.icons.get(IconName.RESUME, IconColor.PRIMARY, IconSize.TOOLBAR),
            "Resume",
            self,
        )
        self.resume_action.setToolTip("Resume selected download(s)")
        self.resume_action.triggered.connect(self._on_resume_selected)
        self.toolbar.addAction(self.resume_action)

        self.pause_action = QAction(
            self.icons.get(IconName.PAUSE, IconColor.WARNING, IconSize.TOOLBAR),
            "Pause",
            self,
        )
        self.pause_action.setToolTip("Pause selected download(s)")
        self.pause_action.triggered.connect(self._on_pause_selected)
        self.toolbar.addAction(self.pause_action)

        self.cancel_action = QAction(
            self.icons.get(IconName.STOP, IconColor.ERROR, IconSize.TOOLBAR),
            "Stop",
            self,
        )
        self.cancel_action.setToolTip("Cancel and stop selected download(s)")
        self.cancel_action.triggered.connect(self._on_cancel_selected)
        self.toolbar.addAction(self.cancel_action)

        self.delete_action = QAction(
            self.icons.get(IconName.DELETE, IconColor.ERROR, IconSize.TOOLBAR),
            "Delete",
            self,
        )
        self.delete_action.setToolTip("Delete selected download record")
        self.delete_action.triggered.connect(self._on_delete_selected)
        self.toolbar.addAction(self.delete_action)

        self.toolbar.addSeparator()

        # Sort Order Menu with icons
        self.sort_btn = QPushButton("Sort")
        self.sort_btn.setIcon(self.icons.get(IconName.SORT, IconColor.SECONDARY, IconSize.TOOLBAR))
        self.sort_menu = QMenu(self)
        self.sort_menu.addAction(
            self.icons.get(IconName.FILE, IconColor.SECONDARY, IconSize.COMPACT),
            "By Name",
            lambda: self._sort_downloads("filename"),
        )
        self.sort_menu.addAction(
            self.icons.get(IconName.DOWNLOAD, IconColor.SECONDARY, IconSize.COMPACT),
            "By Size",
            lambda: self._sort_downloads("size"),
        )
        self.sort_menu.addAction(
            self.icons.get(IconName.CHECK_COMPLETED, IconColor.SECONDARY, IconSize.COMPACT),
            "By Status",
            lambda: self._sort_downloads("status"),
        )
        self.sort_menu.addAction(
            self.icons.get(IconName.WAITING, IconColor.SECONDARY, IconSize.COMPACT),
            "By Date",
            lambda: self._sort_downloads("date"),
        )
        self.sort_btn.setMenu(self.sort_menu)
        self.toolbar.addWidget(self.sort_btn)

        # Settings Action
        settings_action = QAction(
            self.icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.TOOLBAR),
            "Settings",
            self,
        )
        settings_action.triggered.connect(self._on_open_settings)
        self.toolbar.addAction(settings_action)

        # Help Action
        help_action = QAction(
            self.icons.get(IconName.HELP, IconColor.PRIMARY, IconSize.TOOLBAR),
            "Help",
            self,
        )
        help_action.triggered.connect(self._on_open_help)
        self.toolbar.addAction(help_action)

        # Spacer between actions and right controls
        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        self.toolbar.addWidget(spacer)

        # Compact Mode Toggle Switch with icon
        self.mode_toggle_btn = QPushButton("Compact Mode")
        self.mode_toggle_btn.setIcon(
            self.icons.get(IconName.COMPACT_MODE, IconColor.SECONDARY, IconSize.TOOLBAR)
        )
        self.mode_toggle_btn.setCheckable(True)
        self.mode_toggle_btn.setChecked(False)
        self.mode_toggle_btn.clicked.connect(self._toggle_view_mode)
        self.toolbar.addWidget(self.mode_toggle_btn)

        # Search Bar with leading search icon
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search downloads...")
        self.search_edit.addAction(
            self.icons.get(IconName.SEARCH, IconColor.MUTED, IconSize.SMALL),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_edit.setMaximumWidth(220)
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.toolbar.addWidget(self.search_edit)

    def _setup_body(self) -> None:
        """Create main body with splitter hosting sidebar and table view."""
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Expanded Sidebar Widget (page.jfif / page-1.jfif style)
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(6, 8, 6, 8)
        sidebar_layout.setSpacing(6)

        # Section: Downloads
        sidebar_layout.addWidget(QLabel("<b>DOWNLOADS</b>"))
        self.nav_list = QListWidget()
        self.item_all = QListWidgetItem(
            self.icons.get(IconName.ALL_TASKS, IconColor.PRIMARY, IconSize.SIDEBAR),
            "All Tasks",
        )
        self.item_downloading = QListWidgetItem(
            self.icons.get(IconName.DOWNLOADING, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Downloading",
        )
        self.item_waiting = QListWidgetItem(
            self.icons.get(IconName.WAITING, IconColor.WARNING, IconSize.SIDEBAR),
            "Waiting",
        )
        self.item_finished = QListWidgetItem(
            self.icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR),
            "Finished",
        )

        self.nav_list.addItem(self.item_all)
        self.nav_list.addItem(self.item_downloading)
        self.nav_list.addItem(self.item_waiting)
        self.nav_list.addItem(self.item_finished)
        self.nav_list.setCurrentRow(0)
        self.nav_list.itemClicked.connect(self._on_nav_filter_clicked)
        sidebar_layout.addWidget(self.nav_list)

        # Section: Categories (page-1.jfif classic IDM tree)
        sidebar_layout.addWidget(QLabel("<b>CATEGORIES</b>"))
        self.cat_list = QListWidget()
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.DOCUMENT, IconColor.SECONDARY, IconSize.SIDEBAR), "Documents")
        )
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.ARCHIVE, IconColor.SECONDARY, IconSize.SIDEBAR), "Archives")
        )
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.VIDEO, IconColor.SECONDARY, IconSize.SIDEBAR), "Videos")
        )
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.AUDIO, IconColor.SECONDARY, IconSize.SIDEBAR), "Audio")
        )
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.APPLICATION, IconColor.SECONDARY, IconSize.SIDEBAR), "Applications")
        )
        self.cat_list.addItem(
            QListWidgetItem(self.icons.get(IconName.OTHER_FILE, IconColor.SECONDARY, IconSize.SIDEBAR), "Other")
        )
        self.cat_list.itemClicked.connect(self._on_category_filter_clicked)
        sidebar_layout.addWidget(self.cat_list)

        # Section: Engine Status Badge
        sidebar_layout.addStretch()
        status_box = QWidget()
        status_box_layout = QHBoxLayout(status_box)
        status_box_layout.setContentsMargins(6, 4, 6, 4)
        status_box.setStyleSheet(
            "background-color: #064e3b; border-radius: 4px;"
        )

        badge_icon_label = QLabel()
        badge_icon_label.setPixmap(
            self.icons.get(IconName.ENGINE_ACTIVE, IconColor.SUCCESS, IconSize.SIDEBAR).pixmap(16, 16)
        )
        status_box_layout.addWidget(badge_icon_label)

        self.status_pill = QLabel("Engine Active")
        self.status_pill.setStyleSheet("color: #34d399; font-weight: bold;")
        status_box_layout.addWidget(self.status_pill)
        status_box_layout.addStretch()

        sidebar_layout.addWidget(status_box)

        self.splitter.addWidget(self.sidebar_widget)

        # 2. Compact Slim Icon Sidebar Widget (compact.jfif style)
        self.compact_sidebar_widget = QWidget()
        compact_layout = QVBoxLayout(self.compact_sidebar_widget)
        compact_layout.setContentsMargins(4, 8, 4, 8)
        compact_layout.setSpacing(10)

        btn_dl = QPushButton()
        btn_dl.setIcon(self.icons.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.SIDEBAR))
        btn_dl.setToolTip("All Downloads")
        btn_dl.clicked.connect(lambda: self._set_nav_filter("ALL"))
        compact_layout.addWidget(btn_dl)

        btn_queue = QPushButton()
        btn_queue.setIcon(self.icons.get(IconName.QUEUE, IconColor.PRIMARY, IconSize.SIDEBAR))
        btn_queue.setToolTip("Queues")
        btn_queue.clicked.connect(lambda: self._set_nav_filter("WAITING"))
        compact_layout.addWidget(btn_queue)

        btn_done = QPushButton()
        btn_done.setIcon(self.icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR))
        btn_done.setToolTip("Finished Downloads")
        btn_done.clicked.connect(lambda: self._set_nav_filter("FINISHED"))
        compact_layout.addWidget(btn_done)

        btn_add = QPushButton()
        btn_add.setIcon(self.icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.SIDEBAR))
        btn_add.setToolTip("Add Download")
        btn_add.clicked.connect(self._on_add_download)
        compact_layout.addWidget(btn_add)

        compact_layout.addStretch()

        btn_settings = QPushButton()
        btn_settings.setIcon(self.icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.SIDEBAR))
        btn_settings.setToolTip("Settings")
        btn_settings.clicked.connect(self._on_open_settings)
        compact_layout.addWidget(btn_settings)

        self.compact_sidebar_widget.setFixedWidth(52)
        self.compact_sidebar_widget.setVisible(False)
        self.splitter.addWidget(self.compact_sidebar_widget)

        # 3. Main Table Widget
        self.splitter.addWidget(self.table_view)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)

        self._main_layout.addWidget(self.splitter)

    def _setup_footer_statusbar(self) -> None:
        """Create footer status bar showing global throughput and storage."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.footer_status_label = QLabel("Ready.")
        self.status_bar.addWidget(self.footer_status_label, 1)

        self.speed_indicator_label = QLabel("0.00 B/s")
        self.speed_indicator_label.setStyleSheet("color: #89b4fa; font-weight: bold; padding-right: 16px;")
        self.status_bar.addPermanentWidget(self.speed_indicator_label)

    def _toggle_view_mode(self) -> None:
        """Toggle between Expanded Mode (page.jfif) and Compact Mode (compact.jfif)."""
        self._is_compact_mode = self.mode_toggle_btn.isChecked()
        if self._is_compact_mode:
            self.mode_toggle_btn.setText("Expanded Mode")
            self.mode_toggle_btn.setIcon(
                self.icons.get(IconName.EXPANDED_MODE, IconColor.SECONDARY, IconSize.TOOLBAR)
            )
            self.sidebar_widget.setVisible(False)
            self.compact_sidebar_widget.setVisible(True)
            self.profile_combo.setVisible(False)
            self.sort_btn.setVisible(False)
            self.resize(840, 500)
        else:
            self.mode_toggle_btn.setText("Compact Mode")
            self.mode_toggle_btn.setIcon(
                self.icons.get(IconName.COMPACT_MODE, IconColor.SECONDARY, IconSize.TOOLBAR)
            )
            self.sidebar_widget.setVisible(True)
            self.compact_sidebar_widget.setVisible(False)
            self.profile_combo.setVisible(True)
            self.sort_btn.setVisible(True)
            self.resize(1080, 640)

    def _refresh_downloads(self) -> None:
        """Fetch all downloads from database and apply current filters."""
        all_downloads = self.container.download_repo.get_all()

        # Update sidebar badges
        c_all = len(all_downloads)
        c_active = sum(1 for d in all_downloads if d.status == DownloadStatus.DOWNLOADING)
        c_waiting = sum(1 for d in all_downloads if d.status in (DownloadStatus.QUEUED, DownloadStatus.PENDING, DownloadStatus.PAUSED))
        c_done = sum(1 for d in all_downloads if d.status == DownloadStatus.COMPLETED)

        self.item_all.setText(f"All Tasks ({c_all})")
        self.item_downloading.setText(f"Downloading ({c_active})")
        self.item_waiting.setText(f"Waiting ({c_waiting})")
        self.item_finished.setText(f"Finished ({c_done})")

        filtered = all_downloads

        # Apply navigation filter
        if self._current_filter == "DOWNLOADING":
            filtered = [d for d in filtered if d.status == DownloadStatus.DOWNLOADING]
        elif self._current_filter == "WAITING":
            filtered = [d for d in filtered if d.status in (DownloadStatus.QUEUED, DownloadStatus.PENDING, DownloadStatus.PAUSED)]
        elif self._current_filter == "FINISHED":
            filtered = [d for d in filtered if d.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED)]
        elif self._current_filter.startswith("CAT_"):
            cat_name = self._current_filter[4:]
            filtered = [d for d in filtered if d.category.value.upper() == cat_name]

        # Apply search query filter
        if self._search_query:
            q = self._search_query.lower()
            filtered = [d for d in filtered if q in d.filename.lower() or q in d.url.raw.lower()]

        self.table_model.set_downloads(filtered)

    def _on_nav_filter_clicked(self, item: QListWidgetItem) -> None:
        txt = item.text()
        if "All" in txt:
            self._current_filter = "ALL"
        elif "Downloading" in txt:
            self._current_filter = "DOWNLOADING"
        elif "Waiting" in txt:
            self._current_filter = "WAITING"
        elif "Finished" in txt:
            self._current_filter = "FINISHED"
        self._refresh_downloads()

    def _set_nav_filter(self, filter_name: str) -> None:
        self._current_filter = filter_name
        self._refresh_downloads()

    def _on_category_filter_clicked(self, item: QListWidgetItem) -> None:
        txt = item.text().upper()
        if "DOCUMENTS" in txt:
            self._current_filter = f"CAT_{DownloadCategory.DOCUMENTS.value.upper()}"
        elif "ARCHIVES" in txt:
            self._current_filter = f"CAT_{DownloadCategory.ARCHIVES.value.upper()}"
        elif "VIDEOS" in txt:
            self._current_filter = f"CAT_{DownloadCategory.VIDEOS.value.upper()}"
        elif "AUDIO" in txt:
            self._current_filter = f"CAT_{DownloadCategory.AUDIO.value.upper()}"
        elif "APPLICATIONS" in txt:
            self._current_filter = f"CAT_{DownloadCategory.APPLICATIONS.value.upper()}"
        else:
            self._current_filter = f"CAT_{DownloadCategory.OTHER.value.upper()}"
        self._refresh_downloads()

    def _on_search_changed(self, text: str) -> None:
        self._search_query = text.strip()
        self._refresh_downloads()

    def _sort_downloads(self, key: str) -> None:
        downloads = self.container.download_repo.get_all()
        if key == "filename":
            downloads.sort(key=lambda d: d.filename.lower())
        elif key == "size":
            downloads.sort(key=lambda d: d.total_size, reverse=True)
        elif key == "status":
            downloads.sort(key=lambda d: d.status.value)
        elif key == "date":
            downloads.sort(key=lambda d: d.created_at, reverse=True)
        self.table_model.set_downloads(downloads)

    def _on_add_download(self, initial_url: str | None = None) -> None:
        dlg = AddDownloadDialog(self.container.settings.download_dir, self)
        if initial_url:
            dlg.url_edit.setText(initial_url)
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

    def _on_clipboard_url_detected(self, detected_url: str) -> None:
        """Invoked when user copies an HTTP/HTTPS URL with active clipboard monitor."""
        reply = QMessageBox.question(
            self,
            "Download Link Detected",
            f"PyIDM detected a download URL on your clipboard:\n\n{detected_url}\n\nWould you like to download this file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._on_add_download(initial_url=detected_url)

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
        if not dl:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{dl.filename}' from PyIDM?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.container.download_manager.cancel_download(dl.id)
            self.container.download_repo.delete(dl.id)
            self._refresh_downloads()

    def _on_open_settings(self) -> None:
        dlg = SettingsDialog(self.container.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.container.settings.global_speed_limit_bps:
                self.container.download_manager.set_global_speed_limit(
                    self.container.settings.global_speed_limit_bps
                )
            else:
                self.container.download_manager.set_global_speed_limit(None)

    def _on_open_help(self) -> None:
        dlg = HelpDialog(self)
        dlg.exec()

    def _on_table_double_clicked(self) -> None:
        self._on_show_details()

    def _on_show_details(self) -> None:
        dl = self._get_selected_download()
        if not dl:
            return
        segments = self.container.segment_repo.get_by_download_id(dl.id)
        dlg = DownloadDetailsDialog(dl, segments, self)
        dlg.exec()

    def _show_context_menu(self, pos: QPoint) -> None:
        dl = self._get_selected_download()
        if not dl:
            return

        menu = QMenu(self)

        if dl.status in (DownloadStatus.PAUSED, DownloadStatus.PENDING, DownloadStatus.FAILED):
            menu.addAction(
                self.icons.get(IconName.RESUME, IconColor.PRIMARY, IconSize.COMPACT),
                "Resume",
                self._on_resume_selected,
            )
        if dl.status == DownloadStatus.DOWNLOADING:
            menu.addAction(
                self.icons.get(IconName.PAUSE, IconColor.WARNING, IconSize.COMPACT),
                "Pause",
                self._on_pause_selected,
            )

        menu.addAction(
            self.icons.get(IconName.STOP, IconColor.ERROR, IconSize.COMPACT),
            "Stop / Cancel",
            self._on_cancel_selected,
        )
        menu.addSeparator()

        menu.addAction(
            self.icons.get(IconName.FOLDER_OPEN, IconColor.SECONDARY, IconSize.COMPACT),
            "Open Containing Folder",
            lambda: self._open_folder(dl.destination_directory),
        )
        if dl.status == DownloadStatus.COMPLETED:
            menu.addAction(
                self.icons.get(IconName.FILE, IconColor.SECONDARY, IconSize.COMPACT),
                "Open File",
                lambda: self._open_file(dl.final_path),
            )

        menu.addAction(
            self.icons.get(IconName.LINK, IconColor.SECONDARY, IconSize.COMPACT),
            "Copy Download Link",
            lambda: self._copy_link(dl.url.raw),
        )
        menu.addSeparator()

        # Batch Selection Helpers (from page.jfif)
        menu.addAction(
            self.icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.COMPACT),
            "Select Completed Tasks",
            self._select_completed,
        )
        menu.addAction(
            self.icons.get(IconName.CHECK_FAILED, IconColor.ERROR, IconSize.COMPACT),
            "Select Failed Tasks",
            self._select_failed,
        )
        menu.addAction(
            self.icons.get(IconName.SELECT_ALL, IconColor.SECONDARY, IconSize.COMPACT),
            "Select All",
            self.table_view.selectAll,
        )
        menu.addSeparator()

        menu.addAction(
            self.icons.get(IconName.INFO, IconColor.PRIMARY, IconSize.COMPACT),
            "View Details...",
            self._on_show_details,
        )
        menu.addAction(
            self.icons.get(IconName.DELETE, IconColor.ERROR, IconSize.COMPACT),
            "Delete Record",
            self._on_delete_selected,
        )

        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _select_completed(self) -> None:
        for row in range(self.table_model.rowCount()):
            dl = self.table_model.get_download(row)
            if dl and dl.status == DownloadStatus.COMPLETED:
                self.table_view.selectRow(row)

    def _select_failed(self) -> None:
        for row in range(self.table_model.rowCount()):
            dl = self.table_model.get_download(row)
            if dl and dl.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                self.table_view.selectRow(row)

    def _copy_link(self, url: str) -> None:
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(url)

    def _open_folder(self, path: Path) -> None:
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        else:
            QMessageBox.warning(self, "Directory Not Found", f"Cannot find directory: {path}")

    def _open_file(self, file_path: Path) -> None:
        if file_path.exists():
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path)])
        else:
            QMessageBox.warning(self, "File Not Found", f"Cannot find file: {file_path}")

    def _on_progress_updated(
        self, download_id: str, downloaded_bytes: int, total_bytes: int, speed_bps: float, eta_sec: float
    ) -> None:
        self.table_model.update_progress(download_id, downloaded_bytes, total_bytes, speed_bps, eta_sec)
        # Update aggregate speed label
        speed_str = DownloadSpeed(speed_bps).formatted if speed_bps > 0 else "0.00 B/s"
        self.speed_indicator_label.setText(f"Speed: {speed_str}")

    def _on_status_changed(self, download_id: str, status_str: str) -> None:
        self.table_model.update_status(download_id, status_str)
        self._refresh_downloads()

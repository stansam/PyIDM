"""Modularized MainWindow coordinating components, controllers, and services."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
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
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.system.clipboard_monitor import ClipboardMonitor
from app.presentation.delegates.segmented_progress_delegate import (
    SegmentedProgressBarDelegate,
)
from app.presentation.dialogs.download_confirmation_dialog import (
    DownloadConfirmationDialog,
)
from app.presentation.icons import (
    IconColor,
    IconName,
    get_icon_manager,
)
from app.presentation.models.download_table_model import DownloadTableModel
from app.presentation.themes import ThemeManager
from app.windows.main.components.compact_sidebar import CompactSidebarWidget
from app.windows.main.components.download_table import DownloadTableView
from app.windows.main.components.expanded_sidebar import ExpandedSidebarWidget
from app.windows.main.components.status_bar import MainStatusBar
from app.windows.main.components.toolbar import MainToolbar
from app.windows.main.controllers.context_menu import TableContextMenuController
from app.windows.main.controllers.download_actions import DownloadActionsController
from app.windows.main.controllers.download_filter import DownloadFilterController
from app.windows.main.controllers.download_sort import DownloadSortController
from app.windows.main.services.file_open import FileOpenService


class MainWindow(QMainWindow):
    """Main application window presenting the download dashboard and dual-mode controls."""

    def __init__(self, container: Container) -> None:
        super().__init__()
        self.container = container
        self.icons = get_icon_manager()

        # Controllers
        self._filter_ctrl = DownloadFilterController()
        self._sort_ctrl = DownloadSortController()
        self._actions_ctrl = DownloadActionsController()
        self._context_menu_ctrl = TableContextMenuController()
        self._file_service = FileOpenService()

        self.setWindowTitle("PyIDM — Python Internet Download Manager")
        self.setWindowIcon(self.icons.get(IconName.DOWNLOAD, IconColor.PRIMARY))
        self.resize(1080, 640)

        self._is_compact_mode: bool = False

        # Central Layout
        self._central_widget = QWidget()
        self._main_layout = QVBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setCentralWidget(self._central_widget)

        # 1. Header Toolbar Component
        self._toolbar_comp = MainToolbar(
            icons=self.icons,
            on_add=self._on_add_download,
            on_resume=self._on_resume_selected,
            on_pause=self._on_pause_selected,
            on_cancel=self._on_cancel_selected,
            on_delete=self._on_delete_selected,
            on_sort=self._sort_downloads,
            on_settings=self._on_open_settings,
            on_help=self._on_open_help,
            on_toggle_mode=self._toggle_view_mode,
            on_search_changed=self._on_search_changed,
            parent=self,
        )
        self.addToolBar(self._toolbar_comp)

        # 2. Main Body Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 2a. Expanded Sidebar Component
        self._expanded_sidebar = ExpandedSidebarWidget(
            icons=self.icons,
            on_nav_filter_clicked=self._on_nav_filter_clicked,
            on_category_filter_clicked=self._on_category_filter_clicked,
            parent=self,
        )
        self.splitter.addWidget(self._expanded_sidebar)

        # 2b. Compact Sidebar Component
        self._compact_sidebar = CompactSidebarWidget(
            icons=self.icons,
            on_filter_all=lambda: self._set_nav_filter("ALL"),
            on_filter_waiting=lambda: self._set_nav_filter("WAITING"),
            on_filter_finished=lambda: self._set_nav_filter("FINISHED"),
            on_add=self._on_add_download,
            on_settings=self._on_open_settings,
            parent=self,
        )
        self._compact_sidebar.setVisible(False)
        self.splitter.addWidget(self._compact_sidebar)

        # 2c. Table View Component
        self._table_comp = DownloadTableView(
            icons=self.icons,
            on_double_clicked=self._on_table_double_clicked,
            on_context_menu_requested=self._show_context_menu,
            parent=self,
        )
        self.splitter.addWidget(self._table_comp)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)
        self._main_layout.addWidget(self.splitter)

        # 3. Footer Status Bar Component
        self._status_bar_comp = MainStatusBar(parent=self)
        self.setStatusBar(self._status_bar_comp)

        # Wire Signals from Engine Adapter
        self.container.signal_emitter.progress_updated.connect(self._on_progress_updated)
        self.container.signal_emitter.status_changed.connect(self._on_status_changed)
        self.container.signal_emitter.browser_download_requested.connect(
            self._on_browser_download_requested
        )
        self.container.signal_emitter.download_added.connect(
            lambda _id: self._refresh_downloads()
        )

        # Setup Clipboard Monitor
        if self.container.settings.enable_clipboard_monitor:
            self._clipboard_monitor: ClipboardMonitor | None = ClipboardMonitor(
                on_url_detected=self._on_clipboard_url_detected,
                enabled=True,
            )
        else:
            self._clipboard_monitor = None

        self._refresh_downloads()

    # -------------------------------------------------------------------------
    # Backward-Compatible Public Widget Attributes
    # -------------------------------------------------------------------------

    @property
    def toolbar(self) -> QToolBar:
        return self._toolbar_comp

    @property
    def table_model(self) -> DownloadTableModel:
        return self._table_comp.table_model

    @property
    def table_view(self) -> QTableView:
        return self._table_comp

    @property
    def progress_delegate(self) -> SegmentedProgressBarDelegate:
        return self._table_comp.progress_delegate

    @property
    def add_action(self) -> QAction:
        return self._toolbar_comp.add_action

    @property
    def resume_action(self) -> QAction:
        return self._toolbar_comp.resume_action

    @property
    def pause_action(self) -> QAction:
        return self._toolbar_comp.pause_action

    @property
    def cancel_action(self) -> QAction:
        return self._toolbar_comp.cancel_action

    @property
    def delete_action(self) -> QAction:
        return self._toolbar_comp.delete_action

    @property
    def settings_action(self) -> QAction:
        return self._toolbar_comp.settings_action

    @property
    def help_action(self) -> QAction:
        return self._toolbar_comp.help_action

    @property
    def profile_combo(self) -> QComboBox:
        return self._toolbar_comp.profile_combo

    @property
    def sort_btn(self) -> QPushButton:
        return self._toolbar_comp.sort_btn

    @property
    def search_edit(self) -> QLineEdit:
        return self._toolbar_comp.search_edit

    @property
    def mode_toggle_btn(self) -> QPushButton:
        return self._toolbar_comp.mode_toggle_btn

    @property
    def sidebar_widget(self) -> QWidget:
        return self._expanded_sidebar

    @property
    def compact_sidebar_widget(self) -> QWidget:
        return self._compact_sidebar

    @property
    def nav_list(self) -> QListWidget:
        return self._expanded_sidebar.nav_list

    @property
    def cat_list(self) -> QListWidget:
        return self._expanded_sidebar.cat_list

    @property
    def item_all(self) -> QListWidgetItem:
        return self._expanded_sidebar.item_all

    @property
    def item_downloading(self) -> QListWidgetItem:
        return self._expanded_sidebar.item_downloading

    @property
    def item_waiting(self) -> QListWidgetItem:
        return self._expanded_sidebar.item_waiting

    @property
    def item_finished(self) -> QListWidgetItem:
        return self._expanded_sidebar.item_finished

    @property
    def status_bar(self) -> QStatusBar:
        return self._status_bar_comp

    @property
    def footer_status_label(self) -> QWidget:
        return self._status_bar_comp.footer_status_label

    @property
    def speed_indicator_label(self) -> QWidget:
        return self._status_bar_comp.speed_indicator_label

    @property
    def _current_filter(self) -> str:
        return self._filter_ctrl.current_filter

    @_current_filter.setter
    def _current_filter(self, value: str) -> None:
        self._filter_ctrl.current_filter = value

    @property
    def _search_query(self) -> str:
        return self._filter_ctrl.search_query

    @_search_query.setter
    def _search_query(self, value: str) -> None:
        self._filter_ctrl.search_query = value

    # -------------------------------------------------------------------------
    # Backward-Compatible Methods & Event Handlers
    # -------------------------------------------------------------------------

    def _toggle_view_mode(self) -> None:
        """Toggle between Expanded Mode (page.jfif) and Compact Mode (compact.jfif)."""
        self._is_compact_mode = self.mode_toggle_btn.isChecked()
        if self._is_compact_mode:
            self.mode_toggle_btn.setText("Expanded Mode")
            self._toolbar_comp.update_icons(self.icons, is_compact_mode=True)
            self._expanded_sidebar.setVisible(False)
            self._compact_sidebar.setVisible(True)
            self.profile_combo.setVisible(False)
            self.sort_btn.setVisible(False)
            self.resize(840, 500)
        else:
            self.mode_toggle_btn.setText("Compact Mode")
            self._toolbar_comp.update_icons(self.icons, is_compact_mode=False)
            self._expanded_sidebar.setVisible(True)
            self._compact_sidebar.setVisible(False)
            self.profile_combo.setVisible(True)
            self.sort_btn.setVisible(True)
            self.resize(1080, 640)

    def _refresh_downloads(self) -> None:
        """Fetch all downloads from database, calculate counts, and apply current filters."""
        all_downloads = self.container.download_repo.get_all()

        # Update sidebar badge counters
        c_all, c_active, c_waiting, c_done = self._filter_ctrl.compute_badge_counts(all_downloads)
        self._expanded_sidebar.update_counts(c_all, c_active, c_waiting, c_done)

        # Apply navigation and search query filters
        filtered = self._filter_ctrl.apply(all_downloads)
        self.table_model.set_downloads(filtered)

    def _on_nav_filter_clicked(self, item: QListWidgetItem) -> None:
        self._filter_ctrl.current_filter = self._filter_ctrl.parse_nav_item_text(item.text())
        self._refresh_downloads()

    def _set_nav_filter(self, filter_name: str) -> None:
        self._filter_ctrl.set_nav_filter(filter_name)
        self._refresh_downloads()

    def _on_category_filter_clicked(self, item: QListWidgetItem) -> None:
        self._filter_ctrl.current_filter = self._filter_ctrl.parse_category_item_text(item.text())
        self._refresh_downloads()

    def _on_search_changed(self, text: str) -> None:
        self._filter_ctrl.set_search_query(text)
        self._refresh_downloads()

    def _sort_downloads(self, key: str) -> None:
        downloads = self.container.download_repo.get_all()
        sorted_downloads = self._sort_ctrl.sort(downloads, key)
        self.table_model.set_downloads(sorted_downloads)

    def _on_add_download(self, initial_url: str | None = None) -> None:
        dl = self._actions_ctrl.prompt_add_download(
            parent=self,
            default_dir=self.container.settings.download_dir,
            initial_url=initial_url,
        )
        if dl is not None:
            self.container.download_repo.save(dl)
            self._refresh_downloads()
            self.container.download_manager.start_download(dl.id)

    def _on_browser_download_requested(
        self, url_str: str, filename_str: str, page_url: str, size_str: str, connections: int
    ) -> None:
        """Handle incoming download request from browser extension."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

        if self.container.settings.show_browser_download_dialog:
            dialog = DownloadConfirmationDialog(
                url=url_str,
                suggested_filename=filename_str or None,
                default_dir=self.container.settings.download_dir,
                size_str=size_str or None,
                default_connections=connections or self.container.settings.default_connections,
                parent=self,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                final_url, final_name, dest_dir, conns = dialog.get_result()
                try:
                    url = DownloadUrl.parse(final_url)
                except Exception:
                    return

                headers = HttpHeaders()
                if page_url:
                    headers = headers.with_header("Referer", page_url)

                dl = Download(
                    id=create_download_id(),
                    url=url,
                    destination_directory=dest_dir,
                    filename=final_name,
                    custom_headers=headers,
                    connection_count=conns,
                )
                self.container.download_repo.save(dl)
                self._refresh_downloads()
                self.container.download_manager.start_download(dl.id)
        else:
            try:
                url = DownloadUrl.parse(url_str)
            except Exception:
                return

            headers = HttpHeaders()
            if page_url:
                headers = headers.with_header("Referer", page_url)

            existing_names = {d.filename for d in self.container.download_repo.get_all()}
            final_name = FilenameResolver.resolve(filename_str, url, existing_names)

            dl = Download(
                id=create_download_id(),
                url=url,
                destination_directory=self.container.settings.download_dir,
                filename=final_name,
                custom_headers=headers,
                connection_count=connections or self.container.settings.default_connections,
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
        if dl is not None:
            self.container.download_manager.start_download(dl.id)

    def _on_pause_selected(self) -> None:
        dl = self._get_selected_download()
        if dl is not None:
            self.container.download_manager.pause_download(dl.id)

    def _on_cancel_selected(self) -> None:
        dl = self._get_selected_download()
        if dl is not None:
            self.container.download_manager.cancel_download(dl.id)

    def _on_delete_selected(self) -> None:
        dl = self._get_selected_download()
        if dl is None:
            return
        if self._actions_ctrl.prompt_confirm_delete(self, dl.filename):
            self.container.download_manager.cancel_download(dl.id)
            self.container.download_repo.delete(dl.id)
            self._refresh_downloads()

    def _on_open_settings(self) -> None:
        if self._actions_ctrl.show_settings(self, self.container.settings):
            if self.container.settings.global_speed_limit_bps:
                self.container.download_manager.set_global_speed_limit(
                    self.container.settings.global_speed_limit_bps
                )
            else:
                self.container.download_manager.set_global_speed_limit(None)

            app = QApplication.instance()
            if isinstance(app, QApplication):
                ThemeManager.apply_theme(app, self.container.settings.theme)
            self._update_all_icons()

    def _update_all_icons(self) -> None:
        """Refresh all icons across toolbar, sidebars, and views when theme changes."""
        self._toolbar_comp.update_icons(self.icons, self._is_compact_mode)
        self._expanded_sidebar.update_icons(self.icons)
        self._compact_sidebar.update_icons(self.icons)
        self.table_view.viewport().update()

    def _on_open_help(self) -> None:
        self._actions_ctrl.show_help(self)

    def _on_table_double_clicked(self) -> None:
        self._on_show_details()

    def _on_show_details(self) -> None:
        dl = self._get_selected_download()
        if dl is None:
            return
        self._actions_ctrl.show_details(self, dl, self.container.segment_repo)

    def _show_context_menu(self, pos: QPoint) -> None:
        dl = self._get_selected_download()
        if dl is None:
            return

        global_pos = self.table_view.viewport().mapToGlobal(pos)
        self._context_menu_ctrl.show_context_menu(
            parent=self,
            pos=global_pos,
            download=dl,
            icons=self.icons,
            on_resume=self._on_resume_selected,
            on_pause=self._on_pause_selected,
            on_cancel=self._on_cancel_selected,
            on_open_folder=self._open_folder,
            on_open_file=self._open_file,
            on_copy_link=self._copy_link,
            on_select_completed=self._select_completed,
            on_select_failed=self._select_failed,
            on_select_all=self.table_view.selectAll,
            on_show_details=self._on_show_details,
            on_delete=self._on_delete_selected,
        )

    def _select_completed(self) -> None:
        for row in range(self.table_model.rowCount()):
            dl = self.table_model.get_download(row)
            if dl is not None and dl.status == DownloadStatus.COMPLETED:
                self.table_view.selectRow(row)

    def _select_failed(self) -> None:
        for row in range(self.table_model.rowCount()):
            dl = self.table_model.get_download(row)
            if dl is not None and dl.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                self.table_view.selectRow(row)

    def _copy_link(self, url: str) -> None:
        self._file_service.copy_link(url)

    def _open_folder(self, path: Path) -> None:
        self._file_service.open_folder(self, path)

    def _open_file(self, file_path: Path) -> None:
        self._file_service.open_file(self, file_path)

    def _on_progress_updated(
        self, download_id: str, downloaded_bytes: int, total_bytes: int, speed_bps: float, eta_sec: float
    ) -> None:
        self.table_model.update_progress(download_id, downloaded_bytes, total_bytes, speed_bps, eta_sec)
        self._status_bar_comp.set_speed(speed_bps)

    def _on_status_changed(self, download_id: str, status_str: str) -> None:
        self.table_model.update_status(download_id, status_str)
        self._refresh_downloads()


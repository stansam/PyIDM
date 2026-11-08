"""Main toolbar component for PyIDM application window."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolBar,
    QWidget,
)

from app.presentation.icons import (
    IconColor,
    IconManager,
    IconName,
    IconSize,
)


class MainToolbar(QToolBar):
    """Header toolbar providing profile selection, download actions, sort, and search."""

    def __init__(
        self,
        icons: IconManager,
        on_add: Callable[[], None],
        on_resume: Callable[[], None],
        on_pause: Callable[[], None],
        on_cancel: Callable[[], None],
        on_delete: Callable[[], None],
        on_sort: Callable[[str], None],
        on_settings: Callable[[], None],
        on_help: Callable[[], None],
        on_toggle_mode: Callable[[], None],
        on_search_changed: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Main Controls", parent)
        self.setMovable(False)
        self._icons = icons

        # Profile Selector
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Default Profile", "Work", "High-Priority"])
        self.profile_combo.setToolTip("Active download connection profile")
        self.addWidget(self.profile_combo)
        self.addSeparator()

        # Primary Action Buttons
        self.add_action = QAction(
            self._icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.TOOLBAR),
            "New",
            self,
        )
        self.add_action.setToolTip("Add a new download URL")
        self.add_action.triggered.connect(on_add)
        self.addAction(self.add_action)

        self.resume_action = QAction(
            self._icons.get(IconName.RESUME, IconColor.PRIMARY, IconSize.TOOLBAR),
            "Resume",
            self,
        )
        self.resume_action.setToolTip("Resume selected download(s)")
        self.resume_action.triggered.connect(on_resume)
        self.addAction(self.resume_action)

        self.pause_action = QAction(
            self._icons.get(IconName.PAUSE, IconColor.WARNING, IconSize.TOOLBAR),
            "Pause",
            self,
        )
        self.pause_action.setToolTip("Pause selected download(s)")
        self.pause_action.triggered.connect(on_pause)
        self.addAction(self.pause_action)

        self.cancel_action = QAction(
            self._icons.get(IconName.STOP, IconColor.ERROR, IconSize.TOOLBAR),
            "Stop",
            self,
        )
        self.cancel_action.setToolTip("Cancel and stop selected download(s)")
        self.cancel_action.triggered.connect(on_cancel)
        self.addAction(self.cancel_action)

        self.delete_action = QAction(
            self._icons.get(IconName.DELETE, IconColor.ERROR, IconSize.TOOLBAR),
            "Delete",
            self,
        )
        self.delete_action.setToolTip("Delete selected download record")
        self.delete_action.triggered.connect(on_delete)
        self.addAction(self.delete_action)

        self.addSeparator()

        # Sort Order Menu
        self.sort_btn = QPushButton("Sort")
        self.sort_btn.setObjectName("SortButton")
        self.sort_btn.setIcon(self._icons.get(IconName.SORT, IconColor.SECONDARY, IconSize.TOOLBAR))
        self.sort_menu = QMenu(self)
        self.sort_name_action = self.sort_menu.addAction(
            self._icons.get(IconName.FILE, IconColor.SECONDARY, IconSize.COMPACT),
            "By Name",
            lambda: on_sort("filename"),
        )
        self.sort_size_action = self.sort_menu.addAction(
            self._icons.get(IconName.DOWNLOAD, IconColor.SECONDARY, IconSize.COMPACT),
            "By Size",
            lambda: on_sort("size"),
        )
        self.sort_status_action = self.sort_menu.addAction(
            self._icons.get(IconName.CHECK_COMPLETED, IconColor.SECONDARY, IconSize.COMPACT),
            "By Status",
            lambda: on_sort("status"),
        )
        self.sort_date_action = self.sort_menu.addAction(
            self._icons.get(IconName.WAITING, IconColor.SECONDARY, IconSize.COMPACT),
            "By Date",
            lambda: on_sort("date"),
        )
        self.sort_btn.setMenu(self.sort_menu)
        self.addWidget(self.sort_btn)

        # Settings Action
        self.settings_action = QAction(
            self._icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.TOOLBAR),
            "Settings",
            self,
        )
        self.settings_action.triggered.connect(on_settings)
        self.addAction(self.settings_action)

        # Help Action
        self.help_action = QAction(
            self._icons.get(IconName.HELP, IconColor.PRIMARY, IconSize.TOOLBAR),
            "Help",
            self,
        )
        self.help_action.triggered.connect(on_help)
        self.addAction(self.help_action)

        # Spacer between actions and right controls
        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        self.addWidget(spacer)

        # Compact Mode Toggle Switch with icon
        self.mode_toggle_btn = QPushButton("Compact Mode")
        self.mode_toggle_btn.setObjectName("CompactModeButton")
        self.mode_toggle_btn.setIcon(
            self._icons.get(IconName.COMPACT_MODE, IconColor.SECONDARY, IconSize.TOOLBAR)
        )
        self.mode_toggle_btn.setCheckable(True)
        self.mode_toggle_btn.setChecked(False)
        self.mode_toggle_btn.clicked.connect(on_toggle_mode)
        self.addWidget(self.mode_toggle_btn)

        # Search Bar with leading search icon
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search downloads...")
        self.search_action = self.search_edit.addAction(
            self._icons.get(IconName.SEARCH, IconColor.SECONDARY, IconSize.SMALL),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_edit.setMaximumWidth(220)
        self.search_edit.textChanged.connect(on_search_changed)
        self.addWidget(self.search_edit)

    def update_icons(self, icons: IconManager, is_compact_mode: bool) -> None:
        """Refresh all action and button icons when theme changes."""
        self._icons = icons
        self.add_action.setIcon(icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.TOOLBAR))
        self.resume_action.setIcon(icons.get(IconName.RESUME, IconColor.PRIMARY, IconSize.TOOLBAR))
        self.pause_action.setIcon(icons.get(IconName.PAUSE, IconColor.WARNING, IconSize.TOOLBAR))
        self.cancel_action.setIcon(icons.get(IconName.STOP, IconColor.ERROR, IconSize.TOOLBAR))
        self.delete_action.setIcon(icons.get(IconName.DELETE, IconColor.ERROR, IconSize.TOOLBAR))
        self.sort_btn.setIcon(icons.get(IconName.SORT, IconColor.SECONDARY, IconSize.TOOLBAR))
        self.settings_action.setIcon(icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.TOOLBAR))
        self.help_action.setIcon(icons.get(IconName.HELP, IconColor.PRIMARY, IconSize.TOOLBAR))

        if is_compact_mode:
            self.mode_toggle_btn.setIcon(icons.get(IconName.EXPANDED_MODE, IconColor.SECONDARY, IconSize.TOOLBAR))
        else:
            self.mode_toggle_btn.setIcon(icons.get(IconName.COMPACT_MODE, IconColor.SECONDARY, IconSize.TOOLBAR))

        self.search_action.setIcon(icons.get(IconName.SEARCH, IconColor.SECONDARY, IconSize.SMALL))

        self.sort_name_action.setIcon(icons.get(IconName.FILE, IconColor.SECONDARY, IconSize.COMPACT))
        self.sort_size_action.setIcon(icons.get(IconName.DOWNLOAD, IconColor.SECONDARY, IconSize.COMPACT))
        self.sort_status_action.setIcon(icons.get(IconName.CHECK_COMPLETED, IconColor.SECONDARY, IconSize.COMPACT))
        self.sort_date_action.setIcon(icons.get(IconName.WAITING, IconColor.SECONDARY, IconSize.COMPACT))


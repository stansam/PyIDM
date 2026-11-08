"""Expanded navigation sidebar component for PyIDM application window."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.presentation.icons import (
    IconColor,
    IconManager,
    IconName,
    IconSize,
)


class ExpandedSidebarWidget(QWidget):
    """Full-featured navigation sidebar with category hierarchy and engine status."""

    def __init__(
        self,
        icons: IconManager,
        on_nav_filter_clicked: Callable[[QListWidgetItem], None],
        on_category_filter_clicked: Callable[[QListWidgetItem], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icons = icons

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Section: Downloads
        self.downloads_heading = QLabel("DOWNLOADS")
        self.downloads_heading.setObjectName("SidebarHeading")
        layout.addWidget(self.downloads_heading)

        self.nav_list = QListWidget()
        self.item_all = QListWidgetItem(
            self._icons.get(IconName.ALL_TASKS, IconColor.PRIMARY, IconSize.SIDEBAR),
            "All Tasks",
        )
        self.item_downloading = QListWidgetItem(
            self._icons.get(IconName.DOWNLOADING, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Downloading",
        )
        self.item_waiting = QListWidgetItem(
            self._icons.get(IconName.WAITING, IconColor.WARNING, IconSize.SIDEBAR),
            "Waiting",
        )
        self.item_finished = QListWidgetItem(
            self._icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR),
            "Finished",
        )

        self.nav_list.addItem(self.item_all)
        self.nav_list.addItem(self.item_downloading)
        self.nav_list.addItem(self.item_waiting)
        self.nav_list.addItem(self.item_finished)
        self.nav_list.setCurrentRow(0)
        self.nav_list.itemClicked.connect(on_nav_filter_clicked)
        layout.addWidget(self.nav_list)

        # Section: Categories
        self.categories_heading = QLabel("CATEGORIES")
        self.categories_heading.setObjectName("SidebarHeading")
        layout.addWidget(self.categories_heading)

        self.cat_list = QListWidget()
        self.cat_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._cat_item_map: list[tuple[QListWidgetItem, IconName]] = []
        cat_defs: list[tuple[str, IconName]] = [
            ("Documents", IconName.DOCUMENT),
            ("Archives", IconName.ARCHIVE),
            ("Videos", IconName.VIDEO),
            ("Audio", IconName.AUDIO),
            ("Applications", IconName.APPLICATION),
            ("Other", IconName.OTHER_FILE),
        ]
        for label, icon_name in cat_defs:
            item = QListWidgetItem(self._icons.get(icon_name, IconColor.SECONDARY, IconSize.SIDEBAR), label)
            self.cat_list.addItem(item)
            self._cat_item_map.append((item, icon_name))

        self.cat_list.itemClicked.connect(on_category_filter_clicked)
        layout.addWidget(self.cat_list)

        # Section: Engine Status Badge
        layout.addStretch()
        self.status_box = QWidget()
        status_box_layout = QHBoxLayout(self.status_box)
        status_box_layout.setContentsMargins(6, 4, 6, 4)
        self.status_box.setStyleSheet(
            "background-color: #064e3b; border-radius: 4px;"
        )

        self.badge_icon_label = QLabel()
        self.badge_icon_label.setPixmap(
            self._icons.get(IconName.ENGINE_ACTIVE, IconColor.SUCCESS, IconSize.SIDEBAR).pixmap(16, 16)
        )
        status_box_layout.addWidget(self.badge_icon_label)

        self.status_pill = QLabel("Engine Active")
        self.status_pill.setStyleSheet("color: #34d399; font-weight: bold;")
        status_box_layout.addWidget(self.status_pill)
        status_box_layout.addStretch()

        layout.addWidget(self.status_box)

    def update_counts(self, c_all: int, c_active: int, c_waiting: int, c_done: int) -> None:
        """Update badge counts on navigation filter items."""
        self.item_all.setText(f"All Tasks ({c_all})")
        self.item_downloading.setText(f"Downloading ({c_active})")
        self.item_waiting.setText(f"Waiting ({c_waiting})")
        self.item_finished.setText(f"Finished ({c_done})")

    def update_icons(self, icons: IconManager) -> None:
        """Refresh all sidebar icons when application theme changes."""
        self._icons = icons
        self.item_all.setIcon(icons.get(IconName.ALL_TASKS, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.item_downloading.setIcon(icons.get(IconName.DOWNLOADING, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.item_waiting.setIcon(icons.get(IconName.WAITING, IconColor.WARNING, IconSize.SIDEBAR))
        self.item_finished.setIcon(icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR))

        for cat_item, icon_name in self._cat_item_map:
            cat_item.setIcon(icons.get(icon_name, IconColor.SECONDARY, IconSize.SIDEBAR))

        self.badge_icon_label.setPixmap(
            icons.get(IconName.ENGINE_ACTIVE, IconColor.SUCCESS, IconSize.SIDEBAR).pixmap(16, 16)
        )


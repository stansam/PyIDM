"""Compact slim icon sidebar component for PyIDM application window."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.presentation.icons import (
    IconColor,
    IconManager,
    IconName,
    IconSize,
)


class CompactSidebarWidget(QWidget):
    """Minimal icon-only vertical sidebar for compact workspace presentation."""

    def __init__(
        self,
        icons: IconManager,
        on_filter_all: Callable[[], None],
        on_filter_waiting: Callable[[], None],
        on_filter_finished: Callable[[], None],
        on_add: Callable[[], None],
        on_settings: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CompactSidebar")
        self._icons = icons

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(10)

        self.compact_btn_dl = QPushButton()
        self.compact_btn_dl.setIcon(self._icons.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.compact_btn_dl.setToolTip("All Downloads")
        self.compact_btn_dl.clicked.connect(on_filter_all)
        layout.addWidget(self.compact_btn_dl)

        self.compact_btn_queue = QPushButton()
        self.compact_btn_queue.setIcon(self._icons.get(IconName.QUEUE, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.compact_btn_queue.setToolTip("Queues")
        self.compact_btn_queue.clicked.connect(on_filter_waiting)
        layout.addWidget(self.compact_btn_queue)

        self.compact_btn_done = QPushButton()
        self.compact_btn_done.setIcon(self._icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR))
        self.compact_btn_done.setToolTip("Finished Downloads")
        self.compact_btn_done.clicked.connect(on_filter_finished)
        layout.addWidget(self.compact_btn_done)

        self.compact_btn_add = QPushButton()
        self.compact_btn_add.setIcon(self._icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.SIDEBAR))
        self.compact_btn_add.setToolTip("Add Download")
        self.compact_btn_add.clicked.connect(on_add)
        layout.addWidget(self.compact_btn_add)

        layout.addStretch()

        self.compact_btn_settings = QPushButton()
        self.compact_btn_settings.setIcon(self._icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.SIDEBAR))
        self.compact_btn_settings.setToolTip("Settings")
        self.compact_btn_settings.clicked.connect(on_settings)
        layout.addWidget(self.compact_btn_settings)

        self.setFixedWidth(52)

    def update_icons(self, icons: IconManager) -> None:
        """Refresh all compact button icons when application theme changes."""
        self._icons = icons
        self.compact_btn_dl.setIcon(icons.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.compact_btn_queue.setIcon(icons.get(IconName.QUEUE, IconColor.PRIMARY, IconSize.SIDEBAR))
        self.compact_btn_done.setIcon(icons.get(IconName.CHECK_COMPLETED, IconColor.SUCCESS, IconSize.SIDEBAR))
        self.compact_btn_add.setIcon(icons.get(IconName.ADD, IconColor.SUCCESS, IconSize.SIDEBAR))
        self.compact_btn_settings.setIcon(icons.get(IconName.SETTINGS, IconColor.SECONDARY, IconSize.SIDEBAR))


"""Download table component for PyIDM application window."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QTableView,
    QWidget,
)

from app.presentation.delegates.segmented_progress_delegate import (
    SegmentedProgressBarDelegate,
)
from app.presentation.icons import IconManager
from app.presentation.models.download_table_model import DownloadTableModel


class DownloadTableView(QTableView):
    """Data table rendering active, queued, and completed downloads with custom delegates."""

    def __init__(
        self,
        icons: IconManager,
        on_double_clicked: Callable[[], None],
        on_context_menu_requested: Callable[[QPoint], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.table_model = DownloadTableModel(icons=icons)
        self.setModel(self.table_model)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect signals
        self.doubleClicked.connect(lambda _: on_double_clicked())
        self.customContextMenuRequested.connect(on_context_menu_requested)

        # Header stretch configuration
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Install custom segmented progress bar delegate on column 2 (Progress)
        self.progress_delegate = SegmentedProgressBarDelegate(self)
        self.setItemDelegateForColumn(2, self.progress_delegate)


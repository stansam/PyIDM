"""Presentation components package for PyIDM main window."""

from app.windows.main.components.compact_sidebar import CompactSidebarWidget
from app.windows.main.components.download_table import DownloadTableView
from app.windows.main.components.expanded_sidebar import ExpandedSidebarWidget
from app.windows.main.components.status_bar import MainStatusBar
from app.windows.main.components.toolbar import MainToolbar

__all__ = [
    "CompactSidebarWidget",
    "DownloadTableView",
    "ExpandedSidebarWidget",
    "MainStatusBar",
    "MainToolbar",
]


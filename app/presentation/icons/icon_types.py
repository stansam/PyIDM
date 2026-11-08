"""Icon types, semantic names, colors, and dimension presets for PyIDM."""

from __future__ import annotations

from enum import Enum, StrEnum

from PySide6.QtCore import QSize


class IconName(StrEnum):
    """Semantic identifiers for all icons in PyIDM."""

    # Download Lifecycle
    DOWNLOAD = "download"
    DOWNLOAD_FILE = "download_file"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    CANCEL = "cancel"
    DELETE = "delete"
    REMOVE = "remove"
    ADD = "add"
    REFRESH = "refresh"

    # Navigation & Filters
    ALL_TASKS = "all_tasks"
    DOWNLOADING = "downloading"
    WAITING = "waiting"
    CHECK_COMPLETED = "check_completed"
    CHECK_FAILED = "check_failed"
    QUEUE = "queue"
    CLIPBOARD = "clipboard"

    # Category Icons
    DOCUMENT = "document"
    ARCHIVE = "archive"
    VIDEO = "video"
    AUDIO = "audio"
    APPLICATION = "application"
    OTHER_FILE = "other_file"

    # Application & System
    SETTINGS = "settings"
    SEARCH = "search"
    FOLDER = "folder"
    FOLDER_OPEN = "folder_open"
    FILE = "file"
    LINK = "link"
    COPY = "copy"
    PASTE = "paste"
    HISTORY = "history"
    MENU = "menu"
    HELP = "help"
    SORT = "sort"
    GRID = "grid"
    EXTENSION = "extension"
    UPDATE = "update"
    SELECT_ALL = "select_all"
    ENGINE_ACTIVE = "engine_active"

    # Modes
    COMPACT_MODE = "compact_mode"
    EXPANDED_MODE = "expanded_mode"

    # Status & Alerts
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IconColor(StrEnum):
    """Semantic color roles mapped to theme-aware palettes."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    MUTED = "muted"
    DISABLED = "disabled"
    INHERIT = "inherit"


class IconSize(Enum):
    """Standardized icon dimension presets across the interface."""

    SMALL = QSize(14, 14)
    COMPACT = QSize(16, 16)
    SIDEBAR = QSize(18, 18)
    TOOLBAR = QSize(20, 20)
    MEDIUM = QSize(24, 24)
    LARGE = QSize(32, 32)


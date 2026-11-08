"""Centralized semantic icon registry mapping IconName to provider keys."""

from __future__ import annotations

from app.presentation.icons.icon_types import IconName

# Default MDI icon key mappings for QtAwesome
DEFAULT_MDI_REGISTRY: dict[IconName, str] = {
    # Download Actions
    IconName.DOWNLOAD: "mdi6.download",
    IconName.DOWNLOAD_FILE: "mdi6.file-download-outline",
    IconName.PAUSE: "mdi6.pause",
    IconName.RESUME: "mdi6.play",
    IconName.STOP: "mdi6.stop",
    IconName.CANCEL: "mdi6.close-circle-outline",
    IconName.DELETE: "mdi6.delete-outline",
    IconName.REMOVE: "mdi6.minus-circle-outline",
    IconName.ADD: "mdi6.plus",
    IconName.REFRESH: "mdi6.refresh",

    # Navigation & Filters
    IconName.ALL_TASKS: "mdi6.view-list",
    IconName.DOWNLOADING: "mdi6.download",
    IconName.WAITING: "mdi6.clock-outline",
    IconName.CHECK_COMPLETED: "mdi6.check-circle-outline",
    IconName.CHECK_FAILED: "mdi6.close-circle",
    IconName.QUEUE: "mdi6.format-list-numbered",
    IconName.CLIPBOARD: "mdi6.clipboard-text-outline",

    # Categories
    IconName.DOCUMENT: "mdi6.file-document-outline",
    IconName.ARCHIVE: "mdi6.archive-outline",
    IconName.VIDEO: "mdi6.video-outline",
    IconName.AUDIO: "mdi6.music-note",
    IconName.APPLICATION: "mdi6.application",
    IconName.OTHER_FILE: "mdi6.file-question-outline",

    # Application & Actions
    IconName.SETTINGS: "mdi6.cog-outline",
    IconName.SEARCH: "mdi6.magnify",
    IconName.FOLDER: "mdi6.folder-outline",
    IconName.FOLDER_OPEN: "mdi6.folder-open-outline",
    IconName.FILE: "mdi6.file-outline",
    IconName.LINK: "mdi6.link-variant",
    IconName.COPY: "mdi6.content-copy",
    IconName.PASTE: "mdi6.content-paste",
    IconName.HISTORY: "mdi6.history",
    IconName.MENU: "mdi6.menu",
    IconName.HELP: "mdi6.help-circle-outline",
    IconName.SORT: "mdi6.sort-alphabetical-ascending",
    IconName.GRID: "mdi6.view-grid-outline",
    IconName.EXTENSION: "mdi6.puzzle-outline",
    IconName.UPDATE: "mdi6.refresh",
    IconName.SELECT_ALL: "mdi6.select-all",
    IconName.ENGINE_ACTIVE: "mdi6.check-circle",

    # Modes
    IconName.COMPACT_MODE: "mdi6.arrow-collapse",
    IconName.EXPANDED_MODE: "mdi6.arrow-expand",

    # Status & Alerts
    IconName.ERROR: "mdi6.alert-circle-outline",
    IconName.WARNING: "mdi6.alert-outline",
    IconName.INFO: "mdi6.information-outline",
}


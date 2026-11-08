"""PySide6 TableModel managing download rows with efficient cell repainting."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.file_size import FileSize
from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.presentation.icons import (
    IconColor,
    IconManager,
    IconName,
    IconSize,
    get_icon_manager,
)


class DownloadTableModel(QAbstractTableModel):
    """Qt TableModel for the main download dashboard."""

    COLUMNS = [
        "File Name",
        "Size",
        "Progress",
        "Speed",
        "ETA",
        "Status",
        "Category",
    ]

    def __init__(
        self,
        downloads: list[Download] | None = None,
        icons: IconManager | None = None,
    ) -> None:
        super().__init__()
        self._downloads: list[Download] = downloads or []
        self._speeds: dict[str, float] = {}
        self._etas: dict[str, float] = {}
        self._icons = icons or get_icon_manager()

    def rowCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        return len(self._downloads)

    def columnCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        return len(self.COLUMNS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(  # noqa: N802
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or index.row() >= len(self._downloads):
            return None

        dl = self._downloads[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DecorationRole:
            if col == 0:
                return self._icons.get(
                    self._get_category_icon(dl.category),
                    IconColor.PRIMARY,
                    IconSize.COMPACT,
                )
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return dl.filename
            if col == 1:
                return FileSize(dl.total_size).formatted
            if col == 2:
                if dl.total_size > 0:
                    pct = (dl.downloaded_bytes / dl.total_size) * 100.0
                    return f"{pct:.1f}%"
                return f"{FileSize(dl.downloaded_bytes).formatted}"
            if col == 3:
                bps = self._speeds.get(str(dl.id), 0.0)
                return DownloadSpeed(bps).formatted if bps > 0 else "--"
            if col == 4:
                eta = self._etas.get(str(dl.id), -1.0)
                if eta > 0:
                    m, s = divmod(int(eta), 60)
                    h, m = divmod(m, 60)
                    return f"{h:02d}:{m:02d}:{s:02d}"
                return "--"
            if col == 5:
                return dl.status.value
            if col == 6:
                return dl.category.value

        if role == Qt.ItemDataRole.UserRole:
            return dl

        return None

    def set_downloads(self, downloads: list[Download]) -> None:
        self.beginResetModel()
        self._downloads = list(downloads)
        self.endResetModel()

    def get_download(self, row: int) -> Download | None:
        if 0 <= row < len(self._downloads):
            return self._downloads[row]
        return None

    def update_progress(
        self, download_id: str, downloaded_bytes: int, total_bytes: int, speed_bps: float, eta_sec: float
    ) -> None:
        for row, dl in enumerate(self._downloads):
            if str(dl.id) == download_id:
                dl.downloaded_bytes = downloaded_bytes
                if total_bytes > 0:
                    dl.total_size = total_bytes
                self._speeds[download_id] = speed_bps
                self._etas[download_id] = eta_sec

                idx_start = self.index(row, 2)
                idx_end = self.index(row, 4)
                self.dataChanged.emit(idx_start, idx_end, [Qt.ItemDataRole.DisplayRole])
                break

    def update_status(self, download_id: str, status_str: str) -> None:
        for row, dl in enumerate(self._downloads):
            if str(dl.id) == download_id:
                dl.status = DownloadStatus(status_str)
                idx = self.index(row, 5)
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.DisplayRole])
                break

    @staticmethod
    def _get_category_icon(category: DownloadCategory) -> IconName:
        """Map DownloadCategory to corresponding semantic icon identifier."""
        mapping = {
            DownloadCategory.DOCUMENTS: IconName.DOCUMENT,
            DownloadCategory.ARCHIVES: IconName.ARCHIVE,
            DownloadCategory.VIDEOS: IconName.VIDEO,
            DownloadCategory.AUDIO: IconName.AUDIO,
            DownloadCategory.APPLICATIONS: IconName.APPLICATION,
            DownloadCategory.OTHER: IconName.OTHER_FILE,
        }
        return mapping.get(category, IconName.FILE)

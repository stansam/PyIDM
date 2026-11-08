"""Custom QStyledItemDelegate rendering multi-segment progress bars."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.download_status import DownloadStatus


class SegmentedProgressBarDelegate(QStyledItemDelegate):
    """Paints hardware-accelerated segmented progress bars directly into table cells."""

    # Color palette matching dark modern UI (page.jfif / compact.jfif)
    BG_COLOR = QColor("#27272a")  # Zinc-800
    BORDER_COLOR = QColor("#3f3f46")  # Zinc-700
    TEXT_COLOR = QColor("#f4f4f5")  # Zinc-100

    COLOR_COMPLETED = QColor("#10b981")  # Emerald-500
    COLOR_DOWNLOADING = QColor("#3b82f6")  # Blue-500
    COLOR_PAUSED = QColor("#f59e0b")  # Amber-500
    COLOR_FAILED = QColor("#ef4444")  # Red-500
    COLOR_DEFAULT = QColor("#64748b")  # Slate-500

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Paint custom progress bar when rendering the Progress column."""
        data_obj = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data_obj, Download):
            super().paint(painter, option, index)
            return

        download: Download = data_obj

        # Calculate progress ratio
        ratio = 0.0
        if download.total_size > 0:
            ratio = max(0.0, min(1.0, download.downloaded_bytes / download.total_size))
        elif download.status == DownloadStatus.COMPLETED:
            ratio = 1.0

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw selection background if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Inner bar bounds with margins
        margin_x = 8
        margin_y = 6
        bar_rect = QRect(
            option.rect.x() + margin_x,
            option.rect.y() + margin_y,
            max(0, option.rect.width() - (margin_x * 2)),
            max(0, option.rect.height() - (margin_y * 2)),
        )

        radius = 4

        # Background track
        painter.setPen(self.BORDER_COLOR)
        painter.setBrush(self.BG_COLOR)
        painter.drawRoundedRect(bar_rect, radius, radius)

        # Progress fill
        fill_width = int(bar_rect.width() * ratio)
        if fill_width > 0:
            fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_width, bar_rect.height())

            color = self.COLOR_DEFAULT
            if download.status == DownloadStatus.COMPLETED:
                color = self.COLOR_COMPLETED
            elif download.status in (
                DownloadStatus.DOWNLOADING,
                DownloadStatus.INSPECTING,
                DownloadStatus.ASSEMBLING,
                DownloadStatus.VERIFYING,
            ):
                color = self.COLOR_DOWNLOADING
            elif download.status in (DownloadStatus.PAUSED, DownloadStatus.PAUSING, DownloadStatus.QUEUED):
                color = self.COLOR_PAUSED
            elif download.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                color = self.COLOR_FAILED

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(fill_rect, radius, radius)

        # Progress text label (e.g. "75.4%")
        pct_text = f"{ratio * 100.0:.1f}%" if download.total_size > 0 or download.status == DownloadStatus.COMPLETED else "--"
        painter.setPen(self.TEXT_COLOR)
        font = QFont(option.font)
        font.setPointSize(max(8, font.pointSize() - 1))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, pct_text)

        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        """Provide comfortable row height for progress bar painting."""
        base_size = super().sizeHint(option, index)
        return QSize(base_size.width(), max(base_size.height(), 32))


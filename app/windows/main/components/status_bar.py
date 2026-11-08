"""Status bar component for PyIDM application window."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from app.domain.downloads.value_objects.speed import DownloadSpeed


class MainStatusBar(QStatusBar):
    """Application footer status bar displaying global status and aggregate throughput."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.footer_status_label = QLabel("Ready.")
        self.addWidget(self.footer_status_label, 1)

        self.speed_indicator_label = QLabel("0.00 B/s")
        self.speed_indicator_label.setObjectName("SpeedIndicator")
        self.addPermanentWidget(self.speed_indicator_label)

    def set_status(self, text: str) -> None:
        """Set message on main footer status label."""
        self.footer_status_label.setText(text)

    def set_speed(self, speed_bps: float) -> None:
        """Update aggregate download speed indicator."""
        speed_str = DownloadSpeed(speed_bps).formatted if speed_bps > 0 else "0.00 B/s"
        self.speed_indicator_label.setText(f"Speed: {speed_str}")


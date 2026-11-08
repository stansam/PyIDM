"""Add Download dialog prompting for URL, filename, and connection options."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.value_objects.url import DownloadUrl


class AddDownloadDialog(QDialog):
    """Dialog allowing user to configure and enqueue a new download URL."""

    def __init__(self, default_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Download — PyIDM")
        self.resize(520, 240)
        self.selected_dir = default_dir

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/file.zip")
        self.url_edit.textChanged.connect(self._on_url_changed)
        form.addRow("URL:", self.url_edit)

        self.filename_edit = QLineEdit()
        form.addRow("File Name:", self.filename_edit)

        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(str(self.selected_dir))
        self.dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow("Save To:", dir_layout)

        self.conn_spin = QSpinBox()
        self.conn_spin.setRange(1, 32)
        self.conn_spin.setValue(4)
        form.addRow("Connections:", self.conn_spin)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _on_url_changed(self, text: str) -> None:
        try:
            url = DownloadUrl.parse(text)
            resolved = FilenameResolver.resolve(None, url, set())
            self.filename_edit.setText(resolved)
        except Exception:
            pass

    def _on_browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Download Directory", str(self.selected_dir))
        if chosen:
            self.selected_dir = Path(chosen)
            self.dir_edit.setText(str(self.selected_dir))

    def _validate_and_accept(self) -> None:
        url_text = self.url_edit.text().strip()
        try:
            DownloadUrl.parse(url_text)
        except Exception as e:
            QMessageBox.warning(self, "Invalid URL", str(e))
            return

        if not self.filename_edit.text().strip():
            QMessageBox.warning(self, "Invalid Filename", "File name cannot be empty.")
            return

        self.accept()

    def get_result(self) -> tuple[str, str, Path, int]:
        """Returns (url, filename, destination_directory, connections)."""
        return (
            self.url_edit.text().strip(),
            self.filename_edit.text().strip(),
            self.selected_dir,
            self.conn_spin.value(),
        )

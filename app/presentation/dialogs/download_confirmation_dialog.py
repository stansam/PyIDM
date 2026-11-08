"""IDM-style Download Confirmation Dialog prompting for filename, destination, and start options."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.services.category_classifier import CategoryClassifier
from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.value_objects.url import DownloadUrl
from app.presentation.icons import (
    IconColor,
    IconName,
    IconSize,
    get_icon_manager,
)


class DownloadConfirmationDialog(QDialog):
    """Prominent IDM-style download prompt displaying file details and destination."""

    def __init__(
        self,
        url: str,
        suggested_filename: str | None = None,
        default_dir: Path | None = None,
        size_str: str | None = None,
        default_connections: int = 4,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.icons = get_icon_manager()
        self.raw_url = url
        self.selected_dir = default_dir or (Path.home() / "Downloads" / "PyIDM")
        self.start_immediately = True

        self.setWindowTitle("Download File Info — PyIDM")
        self.setWindowIcon(self.icons.get(IconName.DOWNLOAD, IconColor.PRIMARY))
        self.resize(560, 290)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)

        # 1. URL Row
        self.url_edit = QLineEdit(self.raw_url)
        self.url_edit.setReadOnly(True)
        self.url_edit.addAction(
            self.icons.get(IconName.LINK, IconColor.MUTED, IconSize.SMALL),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        form.addRow("URL:", self.url_edit)

        # 2. File Name Row
        try:
            parsed_url = DownloadUrl.parse(self.raw_url)
            initial_name = FilenameResolver.resolve(suggested_filename, parsed_url, set())
        except Exception:
            initial_name = suggested_filename or "download.mp4"

        self.filename_edit = QLineEdit(initial_name)
        self.filename_edit.addAction(
            self.icons.get(IconName.FILE, IconColor.PRIMARY, IconSize.SMALL),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        form.addRow("File Name:", self.filename_edit)

        # 3. Save To Row
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(str(self.selected_dir))
        self.dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setIcon(self.icons.get(IconName.FOLDER_OPEN, IconColor.SECONDARY, IconSize.SMALL))
        browse_btn.clicked.connect(self._on_browse)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow("Save To:", dir_layout)

        # 4. Details Row (File Size & Category)
        details_layout = QHBoxLayout()
        size_display = size_str if size_str and size_str.strip() else "Stream / Unknown Size"
        self.size_label = QLabel(f"<b>{size_display}</b>")
        details_layout.addWidget(self.size_label)

        details_layout.addSpacing(24)
        details_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        for cat in DownloadCategory:
            self.category_combo.addItem(cat.value.capitalize(), cat)
        # Classify automatically
        detected_cat = CategoryClassifier.classify(None, initial_name)
        cat_idx = self.category_combo.findData(detected_cat)
        if cat_idx >= 0:
            self.category_combo.setCurrentIndex(cat_idx)
        details_layout.addWidget(self.category_combo)

        details_layout.addSpacing(24)
        details_layout.addWidget(QLabel("Connections:"))
        self.conn_spin = QSpinBox()
        self.conn_spin.setRange(1, 32)
        self.conn_spin.setValue(default_connections)
        details_layout.addWidget(self.conn_spin)
        form.addRow("Details:", details_layout)

        layout.addLayout(form)
        layout.addStretch()

        # 5. Bottom Action Buttons: 'Start Download' and 'Cancel'
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.start_btn = QPushButton("Start Download")
        self.start_btn.setDefault(True)
        self.start_btn.setStyleSheet("font-weight: bold; padding: 6px 18px;")
        self.start_btn.setIcon(self.icons.get(IconName.RESUME, IconColor.SUCCESS, IconSize.SMALL))
        self.start_btn.clicked.connect(self._on_start_now)
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("padding: 6px 14px;")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _on_browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Save Directory", str(self.selected_dir))
        if chosen:
            self.selected_dir = Path(chosen)
            self.dir_edit.setText(str(self.selected_dir))

    def _on_start_now(self) -> None:
        if self._validate():
            self.start_immediately = True
            self.accept()

    def _validate(self) -> bool:
        if not self.filename_edit.text().strip():
            QMessageBox.warning(self, "Invalid Filename", "File name cannot be empty.")
            return False
        return True

    def get_result(self) -> tuple[str, str, Path, int]:
        """Returns (url, filename, destination_directory, connections)."""
        return (
            self.url_edit.text().strip(),
            self.filename_edit.text().strip(),
            self.selected_dir,
            self.conn_spin.value(),
        )

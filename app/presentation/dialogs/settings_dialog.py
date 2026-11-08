"""Application Settings modal dialog for configuring preferences and engine limits."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.configuration.app_settings import AppSettings
from app.presentation.icons import (
    IconColor,
    IconName,
    IconSize,
    get_icon_manager,
)


class SettingsDialog(QDialog):
    """Configuration dialog for adjusting PyIDM desktop preferences."""

    def __init__(self, current_settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = current_settings
        self.icons = get_icon_manager()

        self.setWindowTitle("Preferences — PyIDM")
        self.setWindowIcon(self.icons.get(IconName.SETTINGS, IconColor.SECONDARY))
        self.resize(540, 360)

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Tab 1: General
        general_tab = QWidget()
        gen_form = QFormLayout(general_tab)
        gen_form.setContentsMargins(12, 12, 12, 12)

        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(str(self.settings.download_dir))
        self.dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setIcon(self.icons.get(IconName.FOLDER_OPEN, IconColor.SECONDARY, IconSize.SMALL))
        browse_btn.clicked.connect(self._on_browse_dir)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        gen_form.addRow("Default Download Folder:", dir_layout)

        self.clipboard_check = QCheckBox("Monitor system clipboard for downloadable URLs")
        self.clipboard_check.setChecked(self.settings.enable_clipboard_monitor)
        gen_form.addRow("Clipboard:", self.clipboard_check)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Modern)", "Light", "System Default"])
        current_theme = self.settings.theme.lower()
        if current_theme == "light":
            theme_idx = 1
        elif current_theme in ("system", "system default"):
            theme_idx = 2
        else:
            theme_idx = 0
        self.theme_combo.setCurrentIndex(theme_idx)
        gen_form.addRow("Theme:", self.theme_combo)

        tabs.addTab(
            general_tab,
            self.icons.get(IconName.SETTINGS, IconColor.PRIMARY, IconSize.SIDEBAR),
            "General",
        )

        # Tab 2: Engine & Network
        engine_tab = QWidget()
        eng_form = QFormLayout(engine_tab)
        eng_form.setContentsMargins(12, 12, 12, 12)

        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(1, 10)
        self.max_downloads_spin.setValue(self.settings.max_concurrent_downloads)
        eng_form.addRow("Max Simultaneous Downloads:", self.max_downloads_spin)

        self.conns_per_dl_spin = QSpinBox()
        self.conns_per_dl_spin.setRange(1, 32)
        self.conns_per_dl_spin.setValue(self.settings.default_connections)
        eng_form.addRow("Default Connections Per File:", self.conns_per_dl_spin)

        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(0, 1_000_000_000)
        self.speed_limit_spin.setSingleStep(100_000)
        self.speed_limit_spin.setSuffix(" B/s (0 = Unlimited)")
        self.speed_limit_spin.setValue(self.settings.global_speed_limit_bps or 0)
        eng_form.addRow("Global Download Speed Limit:", self.speed_limit_spin)

        tabs.addTab(
            engine_tab,
            self.icons.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Engine & Network",
        )

        # Tab 3: Browser Integration
        browser_tab = QWidget()
        br_form = QFormLayout(browser_tab)
        br_form.setContentsMargins(12, 12, 12, 12)

        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(1024, 65535)
        self.api_port_spin.setValue(self.settings.api_port)
        br_form.addRow("Local API Loopback Port:", self.api_port_spin)

        self.api_key_edit = QLineEdit(self.settings.api_secret_key)
        self.api_key_edit.setReadOnly(True)
        br_form.addRow("Secret API Key:", self.api_key_edit)

        # Native Messaging Cross-Browser Controls
        from app.infrastructure.browser.registration import (
            get_browser_status,
            register_all_browsers,
            unregister_all_browsers,
        )

        reg_layout = QHBoxLayout()
        reg_btn = QPushButton("Register All Browsers")
        reg_btn.clicked.connect(lambda: self._on_register_browsers(register_all_browsers))
        unreg_btn = QPushButton("Unregister")
        unreg_btn.clicked.connect(lambda: self._on_unregister_browsers(unregister_all_browsers))
        reg_layout.addWidget(reg_btn)
        reg_layout.addWidget(unreg_btn)
        br_form.addRow("Native Messaging:", reg_layout)

        self.status_label = QLineEdit()
        self.status_label.setReadOnly(True)
        self._refresh_browser_status(get_browser_status)
        br_form.addRow("Active Browsers:", self.status_label)

        tabs.addTab(
            browser_tab,
            self.icons.get(IconName.EXTENSION, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Browser Integration",
        )

        main_layout.addWidget(tabs)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _refresh_browser_status(
        self, get_status_fn: Callable[[], dict[str, bool]] | None = None
    ) -> None:
        if get_status_fn is None:
            from app.infrastructure.browser.registration import get_browser_status

            get_status_fn = get_browser_status
        status = get_status_fn()
        active = [b.capitalize() for b, registered in status.items() if registered]
        if active:
            self.status_label.setText(f"Connected: {', '.join(active)}")
        else:
            self.status_label.setText("No browsers registered")

    def _on_register_browsers(self, register_fn: Callable[[], dict[str, bool]]) -> None:
        register_fn()
        self._refresh_browser_status()

    def _on_unregister_browsers(self, unregister_fn: Callable[[], dict[str, bool]]) -> None:
        unregister_fn()
        self._refresh_browser_status()

    def _on_browse_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.dir_edit.text()
        )
        if chosen:
            self.dir_edit.setText(chosen)

    def _save_and_accept(self) -> None:
        self.settings.download_dir = Path(self.dir_edit.text())
        self.settings.enable_clipboard_monitor = self.clipboard_check.isChecked()
        self.settings.max_concurrent_downloads = self.max_downloads_spin.value()
        self.settings.default_connections = self.conns_per_dl_spin.value()
        limit_val = self.speed_limit_spin.value()
        self.settings.global_speed_limit_bps = limit_val if limit_val > 0 else None
        self.settings.api_port = self.api_port_spin.value()
        theme_map = {0: "dark", 1: "light", 2: "system"}
        self.settings.theme = theme_map.get(self.theme_combo.currentIndex(), "dark")
        self.accept()

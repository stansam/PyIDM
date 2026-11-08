"""Centralized ThemeManager applying stylesheets, palettes, and icon color updates."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.presentation.icons import get_icon_manager


class ThemeManager:
    """Manages application-wide theme switching (Dark, Light, System)."""

    THEMES_DIR = Path(__file__).parent

    @classmethod
    def is_system_dark(cls) -> bool:
        """Detect whether the host operating system is in dark mode."""
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return bool(value == 0)
            except Exception:
                return True
        return True

    @classmethod
    def resolve_theme_name(cls, theme_preference: str) -> str:
        """Resolve 'system' to actual 'dark' or 'light'."""
        pref = theme_preference.lower()
        if pref in ("dark", "dark (modern)"):
            return "dark"
        if pref == "light":
            return "light"
        if pref == "system default" or pref == "system":
            return "dark" if cls.is_system_dark() else "light"
        return "dark"

    @classmethod
    def apply_theme(cls, app: QApplication, theme_preference: str) -> str:
        """Apply the requested theme to QApplication, setting palette, QSS, and icons."""
        theme_name = cls.resolve_theme_name(theme_preference)

        # 1. Configure High-Contrast Native Palette
        palette = QPalette()
        if theme_name == "dark":
            palette.setColor(QPalette.ColorRole.Window, QColor("#181825"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#cdd6f4"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e2e"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#181825"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e1e2e"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#cdd6f4"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#cdd6f4"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#27273a"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#cdd6f4"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#f38ba8"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#a6adc8"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#212529"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f1f3f5"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#212529"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#212529"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#e9ecef"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#212529"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#dc3545"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6c757d"))

        app.setPalette(palette)

        # 2. Load and Apply QSS
        qss_filename = f"{theme_name}.qss"
        qss_path = cls.THEMES_DIR / qss_filename
        if qss_path.is_file():
            with open(qss_path, encoding="utf-8") as f:
                app.setStyleSheet(f.read())

        # 3. Update Centralized IconManager Theme
        icon_mgr = get_icon_manager()
        icon_mgr.set_theme(theme_name)

        return theme_name

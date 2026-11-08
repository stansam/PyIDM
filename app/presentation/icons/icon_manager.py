"""Centralized IconManager providing theme-aware, cached application icons."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.presentation.icons.icon_provider import (
    CustomSvgProvider,
    IconProvider,
    QtAwesomeProvider,
)
from app.presentation.icons.icon_registry import DEFAULT_MDI_REGISTRY
from app.presentation.icons.icon_types import IconColor, IconName, IconSize


class IconManager:
    """Manages icon retrieval, theme-based color mapping, and caching."""

    # Theme Palettes
    PALETTES: dict[str, dict[IconColor, str]] = {
        "dark": {
            IconColor.PRIMARY: "#89b4fa",
            IconColor.SECONDARY: "#cdd6f4",
            IconColor.SUCCESS: "#a6e3a1",
            IconColor.WARNING: "#f9e2af",
            IconColor.ERROR: "#f38ba8",
            IconColor.MUTED: "#6c7086",
            IconColor.DISABLED: "#45475a",
            IconColor.INHERIT: "#cdd6f4",
        },
        "light": {
            IconColor.PRIMARY: "#1e66f5",
            IconColor.SECONDARY: "#4c4f69",
            IconColor.SUCCESS: "#40a02b",
            IconColor.WARNING: "#df8e1d",
            IconColor.ERROR: "#d20f39",
            IconColor.MUTED: "#9ca0b0",
            IconColor.DISABLED: "#bcc0cc",
            IconColor.INHERIT: "#4c4f69",
        },
    }

    def __init__(
        self,
        providers: list[IconProvider] | None = None,
        theme: str = "dark",
        custom_svg_dir: Path | None = None,
    ) -> None:
        self.current_theme = theme if theme in self.PALETTES else "dark"
        self._cache: dict[tuple[str, str, int, int, str], QIcon] = {}

        if providers is not None:
            self.providers = list(providers)
        else:
            self.providers = [
                CustomSvgProvider(custom_svg_dir),
                QtAwesomeProvider(DEFAULT_MDI_REGISTRY),
            ]

    def set_theme(self, theme: str) -> None:
        """Update active theme and clear color-dependent cache if theme changed."""
        normalized = theme.lower()
        new_theme = normalized if normalized in self.PALETTES else "dark"
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self._cache.clear()

    def get_color_hex(self, color: IconColor | str | None) -> str:
        """Resolve semantic IconColor or raw hex string for the active theme."""
        if color is None:
            return self.PALETTES[self.current_theme][IconColor.SECONDARY]
        if isinstance(color, IconColor):
            return self.PALETTES[self.current_theme].get(
                color, self.PALETTES[self.current_theme][IconColor.SECONDARY]
            )
        if isinstance(color, str):
            # Check if it matches an IconColor name
            try:
                enum_val = IconColor(color.lower())
                return self.PALETTES[self.current_theme].get(
                    enum_val, self.PALETTES[self.current_theme][IconColor.SECONDARY]
                )
            except ValueError:
                # Raw hex string
                return color
        return self.PALETTES[self.current_theme][IconColor.SECONDARY]

    def get(
        self,
        name: IconName,
        color: IconColor | str | None = None,
        size: IconSize | QSize | None = None,
    ) -> QIcon:
        """Retrieve a cached or generated QIcon matching requested parameters."""
        # Resolve dimensions
        qsize: QSize
        if size is None:
            qsize = IconSize.TOOLBAR.value
        elif isinstance(size, IconSize):
            qsize = size.value
        else:
            qsize = size

        color_hex = self.get_color_hex(color)
        cache_key = (name.value, color_hex, qsize.width(), qsize.height(), self.current_theme)

        cached_icon = self._cache.get(cache_key)
        if cached_icon is not None and not cached_icon.isNull():
            return cached_icon

        # Resolve icon from registered providers
        icon: QIcon | None = None
        for provider in self.providers:
            if provider.has_icon(name):
                icon = provider.create_icon(name, color_hex, qsize)
                if icon is not None and not icon.isNull():
                    break

        if icon is None or icon.isNull():
            # Graceful fallback: return empty QIcon or safe fallback without raising
            icon = self._create_fallback_icon(color_hex, qsize)

        self._cache[cache_key] = icon
        return icon

    def _create_fallback_icon(self, color_hex: str, size: QSize) -> QIcon:
        """Generate a safe fallback icon if the requested icon was not found."""
        for provider in self.providers:
            if provider.has_icon(IconName.FILE):
                fallback = provider.create_icon(IconName.FILE, color_hex, size)
                if fallback is not None and not fallback.isNull():
                    return fallback
        return QIcon()

    def clear_cache(self) -> None:
        """Clear cached QIcon instances."""
        self._cache.clear()

    # Semantic convenience shortcuts
    def add(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.ADD, color, size)

    def resume(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.RESUME, color, size)

    def pause(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.PAUSE, color, size)

    def stop(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.STOP, color, size)

    def delete(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.DELETE, color, size)

    def settings(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.SETTINGS, color, size)

    def search(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.SEARCH, color, size)

    def folder(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.FOLDER, color, size)

    def file(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.FILE, color, size)

    def help(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.HELP, color, size)

    def completed(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.CHECK_COMPLETED, color or IconColor.SUCCESS, size)

    def error(self, color: IconColor | str | None = None, size: IconSize | QSize | None = None) -> QIcon:
        return self.get(IconName.ERROR, color or IconColor.ERROR, size)


# Global default manager instance
_DEFAULT_ICON_MANAGER: IconManager | None = None


def get_icon_manager() -> IconManager:
    """Return the shared global IconManager instance."""
    global _DEFAULT_ICON_MANAGER
    if _DEFAULT_ICON_MANAGER is None:
        _DEFAULT_ICON_MANAGER = IconManager()
    return _DEFAULT_ICON_MANAGER

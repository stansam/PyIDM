"""Comprehensive unit tests for the centralized IconManager and icon providers."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.presentation.icons import (
    CustomSvgProvider,
    IconColor,
    IconManager,
    IconName,
    IconSize,
    QtAwesomeProvider,
    get_icon_manager,
)


def test_icon_manager_retrieval_and_cache() -> None:
    manager = IconManager()

    # 1. Successful retrieval
    icon1 = manager.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.TOOLBAR)
    assert isinstance(icon1, QIcon)
    assert not icon1.isNull()

    # 2. Cache reuse (same parameters return cached instance)
    icon2 = manager.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.TOOLBAR)
    assert icon1 is icon2

    # 3. Cache separation (different color returns new icon)
    icon3 = manager.get(IconName.DOWNLOAD, IconColor.ERROR, IconSize.TOOLBAR)
    assert icon3 is not icon1
    assert not icon3.isNull()

    # 4. Cache separation (different dimensions)
    icon4 = manager.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.LARGE)
    assert icon4 is not icon1
    assert not icon4.isNull()


def test_icon_manager_semantic_colors() -> None:
    manager = IconManager(theme="dark")

    # Dark theme primary hex
    hex_dark = manager.get_color_hex(IconColor.PRIMARY)
    assert hex_dark == "#89b4fa"

    # Light theme primary hex
    manager.set_theme("light")
    hex_light = manager.get_color_hex(IconColor.PRIMARY)
    assert hex_light == "#1e66f5"

    # Raw hex string passthrough
    custom_hex = manager.get_color_hex("#ff00ff")
    assert custom_hex == "#ff00ff"


def test_icon_manager_theme_switching_clears_cache() -> None:
    manager = IconManager(theme="dark")
    icon_dark = manager.get(IconName.SETTINGS, IconColor.PRIMARY)
    assert not icon_dark.isNull()

    # Switch theme to light
    manager.set_theme("light")
    assert manager.current_theme == "light"
    # Cache should be cleared
    assert len(manager._cache) == 0

    icon_light = manager.get(IconName.SETTINGS, IconColor.PRIMARY)
    assert not icon_light.isNull()


def test_icon_manager_unknown_icon_fallback() -> None:
    # Provider with empty registry
    empty_provider = QtAwesomeProvider({})
    manager = IconManager(providers=[empty_provider])

    # Should not raise exception and return fallback or valid icon
    fallback_icon = manager.get(IconName.DOWNLOAD)
    assert isinstance(fallback_icon, QIcon)


def test_icon_manager_convenience_methods() -> None:
    manager = IconManager()

    assert not manager.add().isNull()
    assert not manager.resume().isNull()
    assert not manager.pause().isNull()
    assert not manager.stop().isNull()
    assert not manager.delete().isNull()
    assert not manager.settings().isNull()
    assert not manager.search().isNull()
    assert not manager.folder().isNull()
    assert not manager.file().isNull()
    assert not manager.help().isNull()
    assert not manager.completed().isNull()
    assert not manager.error().isNull()


def test_custom_svg_provider(tmp_path: Path) -> None:
    # Create a minimal valid SVG file
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="#3b82f6"/>
    </svg>"""
    svg_file = tmp_path / f"{IconName.DOWNLOAD.value}.svg"
    svg_file.write_text(svg_content, encoding="utf-8")

    provider = CustomSvgProvider(resource_dir=tmp_path)
    assert provider.has_icon(IconName.DOWNLOAD)
    assert not provider.has_icon(IconName.SETTINGS)

    icon = provider.create_icon(IconName.DOWNLOAD, "#000000", QSize(24, 24))
    assert icon is not None
    assert not icon.isNull()

    # Missing icon handling
    missing_icon = provider.create_icon(IconName.SETTINGS, "#000000", QSize(24, 24))
    assert missing_icon is None


def test_global_singleton_getter() -> None:
    m1 = get_icon_manager()
    m2 = get_icon_manager()
    assert m1 is m2
    assert isinstance(m1, IconManager)

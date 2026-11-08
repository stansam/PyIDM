"""Icon provider abstractions decoupling presentation components from QtAwesome."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.presentation.icons.icon_types import IconName


class IconProvider(Protocol):
    """Protocol implemented by icon source backends."""

    def has_icon(self, name: IconName) -> bool:
        """Check whether the provider can resolve the given semantic icon name."""
        ...

    def create_icon(self, name: IconName, color_hex: str, size: QSize) -> QIcon | None:
        """Generate a QIcon instance with the requested color and size."""
        ...


class CustomSvgProvider:
    """Loads custom SVG assets from an application resource directory."""

    def __init__(self, resource_dir: Path | None = None) -> None:
        self.resource_dir = resource_dir or (
            Path(__file__).parent.parent / "resources" / "icons" / "custom"
        )

    def has_icon(self, name: IconName) -> bool:
        svg_file = self.resource_dir / f"{name.value}.svg"
        return svg_file.is_file()

    def create_icon(self, name: IconName, color_hex: str, size: QSize) -> QIcon | None:
        svg_file = self.resource_dir / f"{name.value}.svg"
        if not svg_file.is_file():
            return None
        icon = QIcon(str(svg_file))
        return icon if not icon.isNull() else None


class QtAwesomeProvider:
    """Provides Material Design Icons (MDI) via the QtAwesome font library."""

    def __init__(self, registry: dict[IconName, str]) -> None:
        self.registry = registry

    def has_icon(self, name: IconName) -> bool:
        return name in self.registry

    def create_icon(self, name: IconName, color_hex: str, size: QSize) -> QIcon | None:
        mdi_name = self.registry.get(name)
        if not mdi_name:
            return None
        try:
            icon = qta.icon(mdi_name, color=color_hex)
            return QIcon(icon) if not icon.isNull() else None
        except Exception:
            return None

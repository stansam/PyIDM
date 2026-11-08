"""Presentation layer icon management system."""

from app.presentation.icons.icon_manager import IconManager, get_icon_manager
from app.presentation.icons.icon_provider import (
    CustomSvgProvider,
    IconProvider,
    QtAwesomeProvider,
)
from app.presentation.icons.icon_registry import DEFAULT_MDI_REGISTRY
from app.presentation.icons.icon_types import IconColor, IconName, IconSize

__all__ = [
    "DEFAULT_MDI_REGISTRY",
    "CustomSvgProvider",
    "IconColor",
    "IconManager",
    "IconName",
    "IconProvider",
    "IconSize",
    "QtAwesomeProvider",
    "get_icon_manager",
]


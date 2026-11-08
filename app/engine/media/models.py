"""Media models representing detected media formats and extraction variants."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MediaType(StrEnum):
    """Categorization of detected media streams or files."""

    PROGRESSIVE = "PROGRESSIVE"
    HLS = "HLS"
    DASH = "DASH"
    AUDIO_ONLY = "AUDIO_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MediaVariant:
    """Represents a discrete quality rendition or track detected in a media stream."""

    id: str
    url: str
    quality_label: str
    container: str
    resolution: str | None = None
    width: int | None = None
    height: int | None = None
    bitrate_bps: int | None = None
    codecs: str | None = None
    is_audio_only: bool = False
    estimated_size_bytes: int | None = None
    is_drm_protected: bool = False

    @property
    def display_title(self) -> str:
        """Formatted human-readable string for the quality option menu."""
        parts: list[str] = [self.quality_label, self.container.upper()]
        if self.resolution:
            parts.append(self.resolution)
        if self.bitrate_bps and self.bitrate_bps > 0:
            kbps = self.bitrate_bps // 1000
            parts.append(f"{kbps} kbps")
        if self.estimated_size_bytes and self.estimated_size_bytes > 0:
            mb = self.estimated_size_bytes / (1024 * 1024)
            parts.append(f"~{mb:.1f} MB")
        return " • ".join(parts)


@dataclass(frozen=True, slots=True)
class MediaDownloadRequest:
    """Validated media download request originating from a browser extension."""

    url: str
    title: str
    media_type: MediaType = MediaType.PROGRESSIVE
    quality_label: str = "Default"
    container: str = "mp4"
    resolution: str | None = None
    page_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    cookies: str | None = None
    is_drm_protected: bool = False


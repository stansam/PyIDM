"""HLS and DASH media manifest parser extracting quality variants and DRM status."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from app.engine.media.models import MediaVariant

# Regex patterns for HLS EXT-X-STREAM-INF parsing
_HLS_STREAM_INF_RE = re.compile(r"^#EXT-X-STREAM-INF:(.+)$", re.MULTILINE)
_HLS_MEDIA_RE = re.compile(r"^#EXT-X-MEDIA:(.+)$", re.MULTILINE)
_HLS_KEY_RE = re.compile(r"#EXT-X-KEY:METHOD=([^,\s]+)", re.IGNORECASE)


def _parse_hls_attributes(attr_string: str) -> dict[str, str]:
    """Parse comma-separated key=value or key="value" attributes from an HLS tag."""
    attributes: dict[str, str] = {}
    pattern = re.compile(r'([A-Z0-9-]+)=(?:"([^"]*)"|([^,]*))')
    for match in pattern.finditer(attr_string):
        key = match.group(1).strip()
        val = match.group(2) if match.group(2) is not None else match.group(3)
        attributes[key] = val.strip()
    return attributes


class ManifestParser:
    """Parses HLS and DASH manifests into standardized MediaVariant representations."""

    @staticmethod
    def is_hls(content_or_url: str) -> bool:
        """Return True if the text or URL represents an HLS manifest."""
        lower = content_or_url.lower()
        return "#extm3u" in lower or ".m3u8" in lower

    @staticmethod
    def is_dash(content_or_url: str) -> bool:
        """Return True if the text or URL represents a DASH MPD manifest."""
        lower = content_or_url.lower()
        return "<mpd" in lower or ".mpd" in lower

    @classmethod
    def parse_hls(cls, content: str, base_url: str = "") -> list[MediaVariant]:
        """Parse an HLS multivariant/master playlist string into MediaVariant items."""
        # 1. DRM check
        is_drm = False
        for key_match in _HLS_KEY_RE.finditer(content):
            method = key_match.group(1).upper()
            if method not in ("NONE", ""):
                is_drm = True
                break

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        variants: list[MediaVariant] = []

        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line.startswith("#EXT-X-STREAM-INF:"):
                attr_str = line[len("#EXT-X-STREAM-INF:") :]
                attrs = _parse_hls_attributes(attr_str)

                # Next line is the variant URL
                if idx + 1 < len(lines):
                    variant_uri = lines[idx + 1]
                    if not variant_uri.startswith("#"):
                        full_url = urljoin(base_url, variant_uri) if base_url else variant_uri

                        bandwidth_str = attrs.get("BANDWIDTH", "0")
                        bandwidth = int(bandwidth_str) if bandwidth_str.isdigit() else None

                        resolution = attrs.get("RESOLUTION")
                        width: int | None = None
                        height: int | None = None
                        quality_label = "Auto"
                        if resolution and "x" in resolution.lower():
                            parts = resolution.lower().split("x")
                            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                                width = int(parts[0])
                                height = int(parts[1])
                                quality_label = f"{height}p"

                        codecs = attrs.get("CODECS")
                        container = "mp4"

                        variant = MediaVariant(
                            id=f"hls_{len(variants)}_{quality_label}",
                            url=full_url,
                            quality_label=quality_label,
                            container=container,
                            resolution=resolution,
                            width=width,
                            height=height,
                            bitrate_bps=bandwidth,
                            codecs=codecs,
                            is_audio_only=False,
                            is_drm_protected=is_drm,
                        )
                        variants.append(variant)
                        idx += 1
            idx += 1

        # Check for audio-only renditions in #EXT-X-MEDIA:TYPE=AUDIO
        for match in _HLS_MEDIA_RE.finditer(content):
            attrs = _parse_hls_attributes(match.group(1))
            media_type = attrs.get("TYPE", "").upper()
            uri = attrs.get("URI")
            name = attrs.get("NAME", "Audio")
            if media_type == "AUDIO" and uri:
                full_url = urljoin(base_url, uri) if base_url else uri
                variants.append(
                    MediaVariant(
                        id=f"hls_audio_{len(variants)}",
                        url=full_url,
                        quality_label=f"Audio ({name})",
                        container="m4a",
                        is_audio_only=True,
                        is_drm_protected=is_drm,
                    )
                )

        # Sort variants by height / bitrate descending
        variants.sort(
            key=lambda v: (
                0 if v.is_audio_only else 1,
                v.height or 0,
                v.bitrate_bps or 0,
            ),
            reverse=True,
        )
        return variants

    @classmethod
    def parse_dash(cls, xml_content: str, base_url: str = "") -> list[MediaVariant]:
        """Parse a DASH MPD XML string into MediaVariant items."""
        variants: list[MediaVariant] = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return variants

        # XML namespace handling
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # DRM check via ContentProtection elements
        is_drm = bool(root.findall(f".//{ns}ContentProtection"))

        for adaptation_set in root.findall(f".//{ns}AdaptationSet"):
            mime_type = adaptation_set.get("mimeType", "")
            content_type = adaptation_set.get("contentType", "")

            is_video = "video" in mime_type or content_type == "video"
            is_audio = "audio" in mime_type or content_type == "audio"

            for rep in adaptation_set.findall(f"{ns}Representation"):
                rep_id = rep.get("id", f"rep_{len(variants)}")
                bandwidth_str = rep.get("bandwidth", "0")
                bandwidth = int(bandwidth_str) if bandwidth_str.isdigit() else None
                width_str = rep.get("width")
                height_str = rep.get("height")
                width = int(width_str) if width_str and width_str.isdigit() else None
                height = int(height_str) if height_str and height_str.isdigit() else None

                codecs = rep.get("codecs") or adaptation_set.get("codecs")
                container = "webm" if "webm" in mime_type else "mp4"

                if is_audio or (not is_video and "audio" in (mime_type + content_type)):
                    quality_label = f"Audio ({rep_id})"
                    container = "m4a" if container == "mp4" else "ogg"
                    variant = MediaVariant(
                        id=f"dash_{rep_id}",
                        url=base_url,
                        quality_label=quality_label,
                        container=container,
                        bitrate_bps=bandwidth,
                        codecs=codecs,
                        is_audio_only=True,
                        is_drm_protected=is_drm,
                    )
                else:
                    quality_label = f"{height}p" if height else rep_id
                    resolution = f"{width}x{height}" if width and height else None
                    variant = MediaVariant(
                        id=f"dash_{rep_id}",
                        url=base_url,
                        quality_label=quality_label,
                        container=container,
                        resolution=resolution,
                        width=width,
                        height=height,
                        bitrate_bps=bandwidth,
                        codecs=codecs,
                        is_audio_only=False,
                        is_drm_protected=is_drm,
                    )
                variants.append(variant)

        variants.sort(
            key=lambda v: (
                0 if v.is_audio_only else 1,
                v.height or 0,
                v.bitrate_bps or 0,
            ),
            reverse=True,
        )
        return variants

"""Filename resolver service with sanitization and duplicate handling."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from app.domain.downloads.value_objects.url import DownloadUrl

# Regex matching invalid OS filename characters
_INVALID_CHARS_RE = re.compile(r'[\\/*?:"<>|\x00-\x1f]')


class FilenameResolver:
    """Sanitizes filenames and resolves duplicates in target directories."""

    @staticmethod
    def sanitize(filename: str) -> str:
        """Strip path traversal, remove illegal characters, and bound length."""
        cleaned = Path(filename).name  # Strips directory paths / and \
        cleaned = unquote(cleaned)
        cleaned = _INVALID_CHARS_RE.sub("_", cleaned).strip(". ")

        if not cleaned:
            return "download.bin"

        # Truncate base name if needed to ensure max 255 chars
        if len(cleaned.encode("utf-8")) > 255:
            ext = Path(cleaned).suffix
            base = Path(cleaned).stem[: 255 - len(ext.encode("utf-8")) - 4]
            cleaned = f"{base}{ext}"

        return cleaned

    @classmethod
    def resolve(
        cls,
        suggested_name: str | None,
        url: DownloadUrl,
        existing_filenames: set[str],
    ) -> str:
        """Resolve a unique safe filename using suggested name, URL path, or default."""
        candidate: str
        if suggested_name and suggested_name.strip():
            candidate = cls.sanitize(suggested_name)
        elif url.path and url.path.strip("/"):
            candidate = cls.sanitize(Path(url.path).name)
        else:
            candidate = "download.bin"

        if candidate not in existing_filenames:
            return candidate

        # Duplicate resolution: append (1), (2), etc.
        p = Path(candidate)
        stem = p.stem
        suffix = p.suffix
        counter = 1

        while True:
            unique_name = f"{stem} ({counter}){suffix}"
            if unique_name not in existing_filenames:
                return unique_name
            counter += 1


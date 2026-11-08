"""Category classifier service mapping MIME types and extensions to categories."""

from __future__ import annotations

from pathlib import Path

from app.domain.downloads.enums.category import DownloadCategory

_EXTENSION_MAP: dict[str, DownloadCategory] = {
    # Documents
    ".pdf": DownloadCategory.DOCUMENTS,
    ".doc": DownloadCategory.DOCUMENTS,
    ".docx": DownloadCategory.DOCUMENTS,
    ".xls": DownloadCategory.DOCUMENTS,
    ".xlsx": DownloadCategory.DOCUMENTS,
    ".ppt": DownloadCategory.DOCUMENTS,
    ".pptx": DownloadCategory.DOCUMENTS,
    ".txt": DownloadCategory.DOCUMENTS,
    ".epub": DownloadCategory.DOCUMENTS,
    # Applications
    ".exe": DownloadCategory.APPLICATIONS,
    ".msi": DownloadCategory.APPLICATIONS,
    ".dmg": DownloadCategory.APPLICATIONS,
    ".pkg": DownloadCategory.APPLICATIONS,
    ".deb": DownloadCategory.APPLICATIONS,
    ".rpm": DownloadCategory.APPLICATIONS,
    ".appimage": DownloadCategory.APPLICATIONS,
    # Archives
    ".zip": DownloadCategory.ARCHIVES,
    ".rar": DownloadCategory.ARCHIVES,
    ".7z": DownloadCategory.ARCHIVES,
    ".tar": DownloadCategory.ARCHIVES,
    ".gz": DownloadCategory.ARCHIVES,
    ".bz2": DownloadCategory.ARCHIVES,
    ".xz": DownloadCategory.ARCHIVES,
    ".iso": DownloadCategory.ARCHIVES,
    # Videos
    ".mp4": DownloadCategory.VIDEOS,
    ".mkv": DownloadCategory.VIDEOS,
    ".avi": DownloadCategory.VIDEOS,
    ".mov": DownloadCategory.VIDEOS,
    ".webm": DownloadCategory.VIDEOS,
    # Audio
    ".mp3": DownloadCategory.AUDIO,
    ".flac": DownloadCategory.AUDIO,
    ".wav": DownloadCategory.AUDIO,
    ".aac": DownloadCategory.AUDIO,
    ".ogg": DownloadCategory.AUDIO,
    # Images
    ".jpg": DownloadCategory.IMAGES,
    ".jpeg": DownloadCategory.IMAGES,
    ".png": DownloadCategory.IMAGES,
    ".gif": DownloadCategory.IMAGES,
    ".webp": DownloadCategory.IMAGES,
    ".svg": DownloadCategory.IMAGES,
}


class CategoryClassifier:
    """Classifies downloads based on content type and filename extension."""

    @staticmethod
    def classify(content_type: str | None, filename: str) -> DownloadCategory:
        # Check MIME prefix first if present
        if content_type:
            ct = content_type.lower()
            if ct.startswith("video/"):
                return DownloadCategory.VIDEOS
            if ct.startswith("audio/"):
                return DownloadCategory.AUDIO
            if ct.startswith("image/"):
                return DownloadCategory.IMAGES
            if "pdf" in ct or "word" in ct or "sheet" in ct:
                return DownloadCategory.DOCUMENTS
            if "zip" in ct or "tar" in ct or "compressed" in ct:
                return DownloadCategory.ARCHIVES

        # Fallback to extension check
        ext = Path(filename).suffix.lower()
        return _EXTENSION_MAP.get(ext, DownloadCategory.OTHER)


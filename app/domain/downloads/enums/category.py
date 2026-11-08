"""File categorization enum."""

from enum import StrEnum


class DownloadCategory(StrEnum):
    """Broad categories for downloaded content."""

    DOCUMENTS = "DOCUMENTS"
    APPLICATIONS = "APPLICATIONS"
    ARCHIVES = "ARCHIVES"
    VIDEOS = "VIDEOS"
    AUDIO = "AUDIO"
    IMAGES = "IMAGES"
    OTHER = "OTHER"


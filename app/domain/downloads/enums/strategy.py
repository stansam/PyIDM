"""Download execution strategy enum."""

from enum import StrEnum


class DownloadStrategy(StrEnum):
    """Network strategy for file retrieval."""

    SINGLE_STREAM = "SINGLE_STREAM"
    SEGMENTED = "SEGMENTED"


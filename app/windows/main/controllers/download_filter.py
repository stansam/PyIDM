"""Filter state and evaluation logic for downloads."""

from __future__ import annotations

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus


class DownloadFilterController:
    """Manages active filter criteria and evaluates them against download lists."""

    def __init__(self) -> None:
        self.current_filter: str = "ALL"
        self.search_query: str = ""

    def set_nav_filter(self, filter_name: str) -> None:
        """Set active navigation filter (ALL, DOWNLOADING, WAITING, FINISHED, or CAT_...)."""
        self.current_filter = filter_name

    def set_search_query(self, query: str) -> None:
        """Set active text search filter query."""
        self.search_query = query.strip()

    def parse_nav_item_text(self, text: str) -> str:
        """Parse sidebar navigation item label into filter keyword."""
        if "All" in text:
            return "ALL"
        if "Downloading" in text:
            return "DOWNLOADING"
        if "Waiting" in text:
            return "WAITING"
        if "Finished" in text:
            return "FINISHED"
        return "ALL"

    def parse_category_item_text(self, text: str) -> str:
        """Parse category sidebar item label into filter keyword."""
        txt = text.upper()
        if "DOCUMENTS" in txt:
            return f"CAT_{DownloadCategory.DOCUMENTS.value.upper()}"
        if "ARCHIVES" in txt:
            return f"CAT_{DownloadCategory.ARCHIVES.value.upper()}"
        if "VIDEOS" in txt:
            return f"CAT_{DownloadCategory.VIDEOS.value.upper()}"
        if "AUDIO" in txt:
            return f"CAT_{DownloadCategory.AUDIO.value.upper()}"
        if "APPLICATIONS" in txt:
            return f"CAT_{DownloadCategory.APPLICATIONS.value.upper()}"
        return f"CAT_{DownloadCategory.OTHER.value.upper()}"

    def compute_badge_counts(self, all_downloads: list[Download]) -> tuple[int, int, int, int]:
        """Compute task counts for (All, Downloading, Waiting, Finished)."""
        c_all = len(all_downloads)
        c_active = sum(1 for d in all_downloads if d.status == DownloadStatus.DOWNLOADING)
        c_waiting = sum(
            1 for d in all_downloads
            if d.status in (DownloadStatus.QUEUED, DownloadStatus.PENDING, DownloadStatus.PAUSED)
        )
        c_done = sum(1 for d in all_downloads if d.status == DownloadStatus.COMPLETED)
        return (c_all, c_active, c_waiting, c_done)

    def apply(self, downloads: list[Download]) -> list[Download]:
        """Filter download collection using current navigation and search criteria."""
        filtered = downloads

        # 1. Navigation status / category filter
        if self.current_filter == "DOWNLOADING":
            filtered = [d for d in filtered if d.status == DownloadStatus.DOWNLOADING]
        elif self.current_filter == "WAITING":
            filtered = [
                d for d in filtered
                if d.status in (DownloadStatus.QUEUED, DownloadStatus.PENDING, DownloadStatus.PAUSED)
            ]
        elif self.current_filter == "FINISHED":
            filtered = [
                d for d in filtered
                if d.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED)
            ]
        elif self.current_filter.startswith("CAT_"):
            cat_name = self.current_filter[4:]
            filtered = [d for d in filtered if d.category.value.upper() == cat_name]

        # 2. Text search filter
        if self.search_query:
            q = self.search_query.lower()
            filtered = [d for d in filtered if q in d.filename.lower() or q in d.url.raw.lower()]

        return filtered


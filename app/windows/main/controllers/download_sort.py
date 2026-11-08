"""Download sorting logic for table view presentation."""

from __future__ import annotations

from app.domain.downloads.entities.download import Download


class DownloadSortController:
    """Encapsulates sorting algorithms for download entity collections."""

    @staticmethod
    def sort(downloads: list[Download], key: str) -> list[Download]:
        """Return a sorted copy of downloads by the given criterion key."""
        sorted_list = list(downloads)
        if key == "filename":
            sorted_list.sort(key=lambda d: d.filename.lower())
        elif key == "size":
            sorted_list.sort(key=lambda d: d.total_size, reverse=True)
        elif key == "status":
            sorted_list.sort(key=lambda d: d.status.value)
        elif key == "date":
            sorted_list.sort(key=lambda d: d.created_at, reverse=True)
        return sorted_list


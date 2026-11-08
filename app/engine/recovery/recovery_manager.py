"""Startup recovery manager reconciling SQLite state with filesystem manifests."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.downloads.entities.download import Download
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.interfaces.repositories import (
    DownloadRepository,
    SegmentRepository,
)
from app.infrastructure.filesystem.manifest_storage import JsonManifestStorage


@dataclass(frozen=True, slots=True)
class RecoveryCandidate:
    """Represents an unfinished download discovered upon application startup."""

    download: Download
    is_recoverable: bool
    reconciled_bytes: int
    reason: str


class RecoveryManager:
    """Detects and reconciles interrupted downloads after an application crash or restart."""

    def __init__(
        self,
        download_repo: DownloadRepository,
        segment_repo: SegmentRepository,
        manifest_storage: JsonManifestStorage,
    ) -> None:
        self._download_repo = download_repo
        self._segment_repo = segment_repo
        self._manifest_storage = manifest_storage

    def scan_and_reconcile(self) -> list[RecoveryCandidate]:
        """Scan active/interrupted downloads and reconcile disk bytes against database."""
        active_downloads = self._download_repo.get_active()
        candidates: list[RecoveryCandidate] = []

        for dl in active_downloads:
            self._manifest_storage.load(dl.id)
            segments = self._segment_repo.get_by_download_id(dl.id)

            if not segments:
                # No segments recorded, reset to PENDING
                dl.downloaded_bytes = 0
                dl.status = DownloadStatus.PENDING
                self._download_repo.save(dl)
                candidates.append(
                    RecoveryCandidate(
                        download=dl,
                        is_recoverable=True,
                        reconciled_bytes=0,
                        reason="No segments saved, reset to PENDING",
                    )
                )
                continue

            # Verify actual segment file sizes on disk
            reconciled_total = 0
            all_parts_valid = True

            for seg in segments:
                if seg.temp_file_path and seg.temp_file_path.exists():
                    actual_disk_size = seg.temp_file_path.stat().st_size
                    # Clamp downloaded bytes to actual size on disk to prevent forward corruption
                    seg.downloaded_bytes = min(actual_disk_size, seg.byte_range.length)
                    reconciled_total += seg.downloaded_bytes
                    self._segment_repo.update_segment(seg)
                else:
                    seg.downloaded_bytes = 0
                    all_parts_valid = False
                    self._segment_repo.update_segment(seg)

            dl.downloaded_bytes = reconciled_total
            dl.status = DownloadStatus.PAUSED
            self._download_repo.save(dl)

            candidates.append(
                RecoveryCandidate(
                    download=dl,
                    is_recoverable=all_parts_valid or reconciled_total > 0,
                    reconciled_bytes=reconciled_total,
                    reason="Reconciled disk bytes and restored to PAUSED state",
                )
            )

        return candidates

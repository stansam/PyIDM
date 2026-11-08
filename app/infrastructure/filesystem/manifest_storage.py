"""JSON-backed manifest storage for segmented downloads."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.domain.downloads.value_objects.ids import DownloadId
from app.shared.constants import DEFAULT_MANIFEST_NAME


@dataclass
class SegmentRecord:
    id: str
    segment_index: int
    start_byte: int
    end_byte: int
    downloaded_bytes: int
    status: str
    temp_file_path: str | None


@dataclass
class DownloadManifest:
    download_id: str
    total_size: int
    strategy: str
    etag: str | None
    last_modified: str | None
    created_at: str
    segments: list[SegmentRecord]


class JsonManifestStorage:
    """Manages disk manifests (.pyidm_temp/<download_id>/manifest.json) for crash recovery."""

    def __init__(self, temp_base_dir: Path) -> None:
        self._temp_base_dir = temp_base_dir

    def get_manifest_path(self, download_id: DownloadId) -> Path:
        return self._temp_base_dir / str(download_id) / DEFAULT_MANIFEST_NAME

    def save(self, manifest: DownloadManifest) -> None:
        path = self.get_manifest_path(DownloadId(Path(manifest.download_id).name))  # type: ignore[arg-type]
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")

        data = asdict(manifest)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(path)

    def load(self, download_id: DownloadId) -> DownloadManifest | None:
        path = self.get_manifest_path(download_id)
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            segments = [SegmentRecord(**s) for s in data["segments"]]
            return DownloadManifest(
                download_id=data["download_id"],
                total_size=data["total_size"],
                strategy=data["strategy"],
                etag=data.get("etag"),
                last_modified=data.get("last_modified"),
                created_at=data["created_at"],
                segments=segments,
            )
        except Exception:
            return None

    def delete(self, download_id: DownloadId) -> None:
        path = self.get_manifest_path(download_id)
        if path.exists():
            path.unlink()


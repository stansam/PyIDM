"""Atomic file assembly stitching segment chunks into the verified destination file."""

from __future__ import annotations

import os
from pathlib import Path

from app.domain.downloads.entities.segment import DownloadSegment
from app.shared.constants import ASSEMBLING_SUFFIX, DEFAULT_CHUNK_SIZE_BYTES


class FileAssembler:
    """Assembles segmented part files in sequential order with atomic replacement."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES) -> None:
        self._chunk_size = chunk_size

    def assemble(
        self,
        segments: list[DownloadSegment],
        final_destination: Path,
        expected_total_size: int,
    ) -> Path:
        """Stream chunks from sorted segment files into a temp file, then atomically rename."""
        final_destination.parent.mkdir(parents=True, exist_ok=True)
        assembling_path = final_destination.with_suffix(
            final_destination.suffix + ASSEMBLING_SUFFIX
        )

        sorted_segments = sorted(segments, key=lambda s: s.segment_index)

        try:
            with open(assembling_path, "wb") as outfile:
                for seg in sorted_segments:
                    if not seg.temp_file_path or not seg.temp_file_path.exists():
                        raise FileNotFoundError(
                            f"Missing part file for segment {seg.segment_index}: {seg.temp_file_path}"
                        )

                    with open(seg.temp_file_path, "rb") as infile:
                        while True:
                            chunk = infile.read(self._chunk_size)
                            if not chunk:
                                break
                            outfile.write(chunk)

            # Verification
            actual_size = assembling_path.stat().st_size
            if expected_total_size > 0 and actual_size != expected_total_size:
                raise ValueError(
                    f"Assembled file size ({actual_size}) does not match expected ({expected_total_size})"
                )

            # Atomic rename
            os.replace(assembling_path, final_destination)
            return final_destination

        except Exception:
            if assembling_path.exists():
                assembling_path.unlink()
            raise


"""File size value object supporting unknown sizes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileSize:
    """Represents a file size in bytes (-1 if unknown)."""

    bytes: int

    @property
    def is_known(self) -> bool:
        return self.bytes >= 0

    @property
    def as_mb(self) -> float:
        return max(0.0, self.bytes / (1024.0 * 1024.0))

    @property
    def as_gb(self) -> float:
        return max(0.0, self.bytes / (1024.0 * 1024.0 * 1024.0))

    @property
    def formatted(self) -> str:
        if not self.is_known:
            return "Unknown"
        b = float(self.bytes)
        if b < 1024.0:
            return f"{int(b)} B"
        if b < 1024.0 * 1024.0:
            return f"{b / 1024.0:.1f} KB"
        if b < 1024.0 * 1024.0 * 1024.0:
            return f"{b / (1024.0 * 1024.0):.1f} MB"
        return f"{b / (1024.0 * 1024.0 * 1024.0):.2f} GB"


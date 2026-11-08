"""Download speed value object with unit formatting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownloadSpeed:
    """Represents an instantaneous or average transfer rate in bytes per second."""

    bytes_per_second: float

    def __post_init__(self) -> None:
        if self.bytes_per_second < 0.0:
            object.__setattr__(self, "bytes_per_second", 0.0)

    @property
    def as_kbps(self) -> float:
        return self.bytes_per_second / 1024.0

    @property
    def as_mbps(self) -> float:
        return self.bytes_per_second / (1024.0 * 1024.0)

    @property
    def formatted(self) -> str:
        """Human-readable string formatted in B/s, KB/s, or MB/s."""
        bps = self.bytes_per_second
        if bps < 1024.0:
            return f"{bps:.1f} B/s"
        if bps < 1024.0 * 1024.0:
            return f"{bps / 1024.0:.1f} KB/s"
        return f"{bps / (1024.0 * 1024.0):.2f} MB/s"


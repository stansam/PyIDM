"""Byte range value object representing an inclusive HTTP byte offset."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions.domain_errors import InvalidSegmentError


@dataclass(frozen=True, slots=True)
class ByteRange:
    """Inclusive byte range [start, end]."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise InvalidSegmentError(f"Start offset cannot be negative: {self.start}")
        if self.end < self.start:
            raise InvalidSegmentError(
                f"End offset ({self.end}) must be greater than or equal to start ({self.start})"
            )

    @property
    def length(self) -> int:
        """Total byte count spanned by this range."""
        return (self.end - self.start) + 1

    def to_range_header(self) -> str:
        """Generate standard RFC 9110 HTTP Range header value."""
        return f"bytes={self.start}-{self.end}"


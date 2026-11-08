"""Segment calculator service partitioning files into byte ranges."""

from __future__ import annotations

from app.domain.downloads.value_objects.byte_range import ByteRange
from app.shared.constants import MIN_SEGMENT_SIZE_BYTES


class SegmentCalculator:
    """Calculates contiguous non-overlapping ByteRanges for multi-connection downloads."""

    @staticmethod
    def calculate(
        total_size: int,
        connection_count: int,
        min_segment_bytes: int = MIN_SEGMENT_SIZE_BYTES,
    ) -> list[ByteRange]:
        """Divide total_size into up to connection_count contiguous ByteRange slices."""
        if total_size <= 0:
            return []

        # If file is too small, use a single range
        if total_size < min_segment_bytes or connection_count <= 1:
            return [ByteRange(start=0, end=total_size - 1)]

        # Determine effective connection count based on minimum segment size
        max_possible_connections = total_size // min_segment_bytes
        effective_connections = min(connection_count, max_possible_connections)
        effective_connections = max(1, effective_connections)

        segment_size = total_size // effective_connections
        ranges: list[ByteRange] = []
        current_start = 0

        for i in range(effective_connections):
            if i == effective_connections - 1:
                # Last segment absorbs any remaining bytes
                ranges.append(ByteRange(start=current_start, end=total_size - 1))
            else:
                current_end = current_start + segment_size - 1
                ranges.append(ByteRange(start=current_start, end=current_end))
                current_start = current_end + 1

        return ranges


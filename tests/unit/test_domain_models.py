"""Unit tests for domain models, value objects, and business services."""

from pathlib import Path

import pytest

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.enums.segment_status import SegmentStatus
from app.domain.downloads.services.category_classifier import CategoryClassifier
from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.services.segment_calculator import SegmentCalculator
from app.domain.downloads.services.state_validator import DownloadStateValidator
from app.domain.downloads.value_objects.byte_range import ByteRange
from app.domain.downloads.value_objects.file_size import FileSize
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import (
    create_download_id,
    create_segment_id,
)
from app.domain.downloads.value_objects.retry_policy import RetryPolicy
from app.domain.downloads.value_objects.speed import DownloadSpeed
from app.domain.downloads.value_objects.url import DownloadUrl
from app.domain.exceptions.domain_errors import (
    InvalidSegmentError,
    InvalidTransitionError,
    InvalidUrlError,
)


def test_byte_range_properties() -> None:
    br = ByteRange(start=0, end=999)
    assert br.length == 1000
    assert br.to_range_header() == "bytes=0-999"


def test_byte_range_invalid() -> None:
    with pytest.raises(InvalidSegmentError):
        ByteRange(start=-1, end=100)
    with pytest.raises(InvalidSegmentError):
        ByteRange(start=200, end=100)


def test_speed_formatting() -> None:
    assert DownloadSpeed(500.0).formatted == "500.0 B/s"
    assert DownloadSpeed(1048576.0).formatted == "1.00 MB/s"
    assert DownloadSpeed(2048.0).formatted == "2.0 KB/s"


def test_file_size_formatting() -> None:
    assert FileSize(-1).formatted == "Unknown"
    assert FileSize(1024).formatted == "1.0 KB"
    assert FileSize(10485760).formatted == "10.0 MB"
    assert FileSize(5368709120).formatted == "5.00 GB"


def test_url_parsing_and_validation() -> None:
    url = DownloadUrl.parse("https://releases.ubuntu.com/24.04/ubuntu.iso")
    assert url.scheme == "https"
    assert url.host == "releases.ubuntu.com"
    assert url.path == "/24.04/ubuntu.iso"

    with pytest.raises(InvalidUrlError):
        DownloadUrl.parse("ftp://example.com/file.zip")
    with pytest.raises(InvalidUrlError):
        DownloadUrl.parse("not_a_url")


def test_http_headers_case_insensitivity() -> None:
    h = HttpHeaders({"Content-Type": "application/zip", "X-Custom": "val"})
    assert h.get("content-type") == "application/zip"
    assert h.get("CONTENT-TYPE") == "application/zip"
    assert "x-custom" in h
    assert h.get("non-existent") is None

    updated = h.with_header("New-Header", "123")
    assert updated.get("new-header") == "123"
    assert "new-header" not in h  # Original unchanged


def test_retry_policy_delays() -> None:
    policy = RetryPolicy(base_delay_seconds=2.0, max_delay_seconds=10.0, jitter=False)
    assert policy.delay_for_attempt(1) == 2.0
    assert policy.delay_for_attempt(2) == 4.0
    assert policy.delay_for_attempt(3) == 8.0
    assert policy.delay_for_attempt(4) == 10.0  # Capped at max


def test_state_validator_transitions() -> None:
    # Valid transitions
    DownloadStateValidator.validate(DownloadStatus.PENDING, DownloadStatus.INSPECTING)
    DownloadStateValidator.validate(DownloadStatus.DOWNLOADING, DownloadStatus.PAUSING)
    DownloadStateValidator.validate(DownloadStatus.PAUSING, DownloadStatus.PAUSED)
    DownloadStateValidator.validate(DownloadStatus.PAUSED, DownloadStatus.RESUMING)
    DownloadStateValidator.validate(DownloadStatus.RESUMING, DownloadStatus.DOWNLOADING)
    DownloadStateValidator.validate(DownloadStatus.DOWNLOADING, DownloadStatus.VERIFYING)
    DownloadStateValidator.validate(DownloadStatus.VERIFYING, DownloadStatus.ASSEMBLING)
    DownloadStateValidator.validate(DownloadStatus.ASSEMBLING, DownloadStatus.COMPLETED)

    # Invalid transitions
    with pytest.raises(InvalidTransitionError):
        DownloadStateValidator.validate(DownloadStatus.PENDING, DownloadStatus.COMPLETED)
    with pytest.raises(InvalidTransitionError):
        DownloadStateValidator.validate(DownloadStatus.COMPLETED, DownloadStatus.DOWNLOADING)


def test_segment_calculator() -> None:
    # Uneven partition: 10,000,000 bytes across 4 connections
    ranges = SegmentCalculator.calculate(
        total_size=10_000_000, connection_count=4, min_segment_bytes=1_000_000
    )
    assert len(ranges) == 4
    assert ranges[0].start == 0
    assert ranges[3].end == 9_999_999
    # Contiguity check
    assert ranges[0].end + 1 == ranges[1].start
    assert ranges[1].end + 1 == ranges[2].start
    assert ranges[2].end + 1 == ranges[3].start
    total_bytes = sum(r.length for r in ranges)
    assert total_bytes == 10_000_000


def test_filename_resolver() -> None:
    url = DownloadUrl.parse("https://example.com/downloads/archive.tar.gz")
    name = FilenameResolver.resolve(None, url, set())
    assert name == "archive.tar.gz"

    # Duplicate resolution
    name2 = FilenameResolver.resolve(None, url, {"archive.tar.gz"})
    assert name2 == "archive.tar (1).gz"

    # Path traversal sanitization
    unsafe = FilenameResolver.sanitize("../../../windows/system32/cmd.exe")
    assert unsafe == "cmd.exe"


def test_category_classifier() -> None:
    assert CategoryClassifier.classify("video/mp4", "movie.mp4") == DownloadCategory.VIDEOS
    assert CategoryClassifier.classify("application/pdf", "doc.pdf") == DownloadCategory.DOCUMENTS
    assert CategoryClassifier.classify(None, "setup.exe") == DownloadCategory.APPLICATIONS
    assert CategoryClassifier.classify(None, "backup.zip") == DownloadCategory.ARCHIVES
    assert CategoryClassifier.classify(None, "photo.png") == DownloadCategory.IMAGES


def test_download_entity_lifecycle() -> None:
    dl = Download(
        id=create_download_id(),
        url=DownloadUrl.parse("https://example.com/test.zip"),
        destination_directory=Path("/tmp"),
        filename="test.zip",
        total_size=1000,
    )
    assert dl.status == DownloadStatus.PENDING
    assert dl.final_path == Path("/tmp/test.zip")

    dl.transition_to(DownloadStatus.INSPECTING)
    dl.transition_to(DownloadStatus.DOWNLOADING)
    assert dl.is_active is True

    prog = dl.to_progress(current_speed_bps=500.0)
    assert prog.speed.bytes_per_second == 500.0

    dl.transition_to(DownloadStatus.PAUSING)
    dl.transition_to(DownloadStatus.PAUSED)
    current_status: DownloadStatus = dl.status
    assert current_status == DownloadStatus.PAUSED


def test_download_segment_lifecycle() -> None:
    seg = DownloadSegment(
        id=create_segment_id(),
        download_id=create_download_id(),
        segment_index=0,
        byte_range=ByteRange(start=0, end=999),
    )
    assert seg.remaining_bytes == 1000
    assert seg.is_complete is False

    seg.record_progress(500)
    assert seg.downloaded_bytes == 500
    assert seg.current_offset == 500
    assert seg.is_complete is False

    seg.record_progress(500)
    assert seg.downloaded_bytes == 1000
    assert seg.is_complete is True
    assert seg.status == SegmentStatus.COMPLETED


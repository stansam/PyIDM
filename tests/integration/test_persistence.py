"""Integration tests for SQLite persistence, WAL mode, and repository CRUD."""

from pathlib import Path

from app.domain.downloads.entities.download import Download
from app.domain.downloads.entities.segment import DownloadSegment
from app.domain.downloads.enums.category import DownloadCategory
from app.domain.downloads.enums.download_status import DownloadStatus
from app.domain.downloads.value_objects.byte_range import ByteRange
from app.domain.downloads.value_objects.ids import (
    create_download_id,
    create_segment_id,
)
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.persistence.database import (
    create_session_factory,
    create_sqlite_engine,
    init_database,
)
from app.infrastructure.persistence.repositories import (
    SqlDownloadRepository,
    SqlSegmentRepository,
)


def test_sqlite_persistence_crud(tmp_path: Path) -> None:
    db_file = tmp_path / "test_pyidm.db"
    engine = create_sqlite_engine(db_file)
    init_database(engine)
    session_factory = create_session_factory(engine)

    dl_repo = SqlDownloadRepository(session_factory)
    seg_repo = SqlSegmentRepository(session_factory)

    # 1. Save Download
    dl_id = create_download_id()
    download = Download(
        id=dl_id,
        url=DownloadUrl.parse("https://example.com/ubuntu-desktop.iso"),
        destination_directory=tmp_path,
        filename="ubuntu-desktop.iso",
        total_size=4_000_000_000,
        category=DownloadCategory.ARCHIVES,
    )
    dl_repo.save(download)

    # 2. Retrieve Download
    fetched = dl_repo.get_by_id(dl_id)
    assert fetched is not None
    assert fetched.id == dl_id
    assert fetched.filename == "ubuntu-desktop.iso"
    assert fetched.total_size == 4_000_000_000
    assert fetched.status == DownloadStatus.PENDING

    # 3. Add Segments
    seg1 = DownloadSegment(
        id=create_segment_id(),
        download_id=dl_id,
        segment_index=0,
        byte_range=ByteRange(start=0, end=1_999_999_999),
        downloaded_bytes=500_000,
    )
    seg2 = DownloadSegment(
        id=create_segment_id(),
        download_id=dl_id,
        segment_index=1,
        byte_range=ByteRange(start=2_000_000_000, end=3_999_999_999),
        downloaded_bytes=0,
    )
    seg_repo.save_all([seg1, seg2])

    # 4. Fetch Segments
    segments = seg_repo.get_by_download_id(dl_id)
    assert len(segments) == 2
    assert segments[0].downloaded_bytes == 500_000
    assert segments[1].downloaded_bytes == 0

    # 5. Update Status
    dl_repo.update_status(dl_id, DownloadStatus.DOWNLOADING)
    updated = dl_repo.get_by_id(dl_id)
    assert updated is not None
    assert updated.status == DownloadStatus.DOWNLOADING

    # Active downloads query
    active = dl_repo.get_active()
    assert len(active) == 1
    assert active[0].id == dl_id

    # 6. Update Segment
    seg1.record_progress(500_000)
    seg_repo.update_segment(seg1)
    segs_after = seg_repo.get_by_download_id(dl_id)
    assert segs_after[0].downloaded_bytes == 1_000_000

    # 7. Delete Download and Cascade
    dl_repo.delete(dl_id)
    assert dl_repo.get_by_id(dl_id) is None
    # Verify segments cascade deleted
    assert len(seg_repo.get_by_download_id(dl_id)) == 0


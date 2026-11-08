"""Headless GUI tests using pytest-qt and QAbstractTableModel verification."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from pytestqt.qtbot import QtBot

from app.application.container import Container
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
from app.infrastructure.configuration.app_settings import AppSettings
from app.presentation.delegates.segmented_progress_delegate import (
    SegmentedProgressBarDelegate,
)
from app.presentation.dialogs.download_details_dialog import DownloadDetailsDialog
from app.presentation.dialogs.help_dialog import HelpDialog
from app.presentation.dialogs.settings_dialog import SettingsDialog
from app.presentation.models.download_table_model import DownloadTableModel
from app.presentation.windows.main_window import MainWindow


def test_download_table_model_data_and_updates() -> None:
    dl_id = create_download_id()
    download = Download(
        id=dl_id,
        url=DownloadUrl.parse("https://example.com/test.zip"),
        destination_directory=Path("/tmp"),
        filename="test.zip",
        total_size=2_000_000,
        downloaded_bytes=1_000_000,
    )

    model = DownloadTableModel([download])
    assert model.rowCount() == 1
    assert model.columnCount() == 7

    # File name column
    assert model.data(model.index(0, 0)) == "test.zip"
    # Percentage column
    assert model.data(model.index(0, 2)) == "50.0%"
    # Status column
    assert model.data(model.index(0, 5)) == "PENDING"

    # Test dynamic update
    model.update_progress(str(dl_id), 1_500_000, 2_000_000, 500_000.0, 1.0)
    assert model.data(model.index(0, 2)) == "75.0%"

    model.update_status(str(dl_id), "DOWNLOADING")
    assert model.data(model.index(0, 5)) == "DOWNLOADING"


def test_main_window_headless(qtbot: QtBot, tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "gui_test.db",
    )
    container = Container(settings)

    window = MainWindow(container)
    qtbot.addWidget(window)
    window.show()

    assert window.windowTitle().startswith("PyIDM")
    assert window.table_model.rowCount() == 0


def test_main_window_dual_mode_toggle(qtbot: QtBot, tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "gui_test2.db",
    )
    container = Container(settings)

    window = MainWindow(container)
    qtbot.addWidget(window)
    window.show()

    # Initial mode is Expanded Mode
    assert not window._is_compact_mode
    assert window.sidebar_widget.isVisible()
    assert not window.compact_sidebar_widget.isVisible()

    # Toggle to Compact Mode
    window.mode_toggle_btn.click()

    assert window._is_compact_mode
    assert not window.sidebar_widget.isVisible()
    assert window.compact_sidebar_widget.isVisible()

    # Toggle back to Expanded Mode
    window.mode_toggle_btn.click()

    assert not window._is_compact_mode
    assert window.sidebar_widget.isVisible()
    assert not window.compact_sidebar_widget.isVisible()


def test_main_window_search_filter(qtbot: QtBot, tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "gui_test3.db",
    )
    container = Container(settings)

    dl1 = Download(
        id=create_download_id(),
        url=DownloadUrl.parse("https://example.com/alpha-setup.exe"),
        destination_directory=tmp_path,
        filename="alpha-setup.exe",
        status=DownloadStatus.COMPLETED,
        category=DownloadCategory.APPLICATIONS,
    )
    dl2 = Download(
        id=create_download_id(),
        url=DownloadUrl.parse("https://example.com/beta-manual.pdf"),
        destination_directory=tmp_path,
        filename="beta-manual.pdf",
        status=DownloadStatus.PENDING,
        category=DownloadCategory.DOCUMENTS,
    )
    container.download_repo.save(dl1)
    container.download_repo.save(dl2)

    window = MainWindow(container)
    qtbot.addWidget(window)
    window.show()

    assert window.table_model.rowCount() == 2

    # Search for "alpha"
    window.search_edit.setText("alpha")
    assert window.table_model.rowCount() == 1
    assert window.table_model.data(window.table_model.index(0, 0)) == "alpha-setup.exe"

    # Clear search
    window.search_edit.setText("")
    assert window.table_model.rowCount() == 2


def test_download_details_dialog(qtbot: QtBot, tmp_path: Path) -> None:
    dl = Download(
        id=create_download_id(),
        url=DownloadUrl.parse("https://example.com/movie.mkv"),
        destination_directory=tmp_path,
        filename="movie.mkv",
        total_size=10_000_000,
        downloaded_bytes=5_000_000,
        status=DownloadStatus.DOWNLOADING,
        etag='"etag123"',
    )
    seg = DownloadSegment(
        id=create_segment_id(),
        download_id=dl.id,
        segment_index=0,
        byte_range=ByteRange(0, 4_999_999),
        downloaded_bytes=5_000_000,
    )

    dlg = DownloadDetailsDialog(dl, [seg])
    qtbot.addWidget(dlg)
    dlg.show()
    assert dlg.windowTitle().startswith("Download Details")


def test_settings_dialog(qtbot: QtBot, tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "test.db",
        default_connections=4,
    )
    dlg = SettingsDialog(settings)
    qtbot.addWidget(dlg)
    dlg.show()

    dlg.conns_per_dl_spin.setValue(8)
    dlg._save_and_accept()

    assert settings.default_connections == 8


def test_segmented_progress_delegate(tmp_path: Path) -> None:
    dl = Download(
        id=create_download_id(),
        url=DownloadUrl.parse("https://example.com/test.zip"),
        destination_directory=tmp_path,
        filename="test.zip",
        total_size=2_000_000,
        downloaded_bytes=1_000_000,
    )
    model = DownloadTableModel([dl])
    delegate = SegmentedProgressBarDelegate()
    idx = model.index(0, 2)
    from PySide6.QtWidgets import QStyleOptionViewItem
    opt = QStyleOptionViewItem()
    size = delegate.sizeHint(opt, idx)
    assert isinstance(size, QSize)
    assert size.height() >= 32


def test_help_dialog(qtbot: QtBot) -> None:
    dlg = HelpDialog()
    qtbot.addWidget(dlg)
    dlg.show()
    assert dlg.windowTitle().startswith("PyIDM")

"""Headless GUI tests using pytest-qt and QAbstractTableModel verification."""

from pathlib import Path

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.infrastructure.configuration.app_settings import AppSettings
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


def test_main_window_headless(qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
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

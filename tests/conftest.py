"""Shared root test fixtures and environment configuration."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    """Provides an isolated clean directory for download outputs."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


@pytest.fixture
def tmp_temp_dir(tmp_path: Path) -> Path:
    """Provides an isolated clean directory for temporary chunk storage."""
    temp_dir = tmp_path / ".pyidm_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


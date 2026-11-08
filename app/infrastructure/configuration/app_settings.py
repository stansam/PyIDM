"""Application settings backed by Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.shared.constants import (
    DEFAULT_CHUNK_SIZE_BYTES,
    DEFAULT_CONNECTIONS_PER_DOWNLOAD,
    DEFAULT_LOOPBACK_HOST,
    DEFAULT_LOOPBACK_PORT,
)


class AppSettings(BaseSettings):
    """Strongly typed application configuration."""

    download_dir: Path = Field(
        default_factory=lambda: Path.home() / "Downloads" / "PyIDM"
    )
    temp_dir: Path = Field(
        default_factory=lambda: Path.home() / "Downloads" / "PyIDM" / ".pyidm_temp"
    )
    db_path: Path = Field(
        default_factory=lambda: Path.home() / ".pyidm" / "pyidm.db"
    )
    max_concurrent_downloads: int = 3
    default_connections: int = DEFAULT_CONNECTIONS_PER_DOWNLOAD
    chunk_size_bytes: int = DEFAULT_CHUNK_SIZE_BYTES
    global_speed_limit_bps: int | None = None
    theme: str = "dark"
    enable_clipboard_monitor: bool = False
    show_browser_download_dialog: bool = True
    api_host: str = DEFAULT_LOOPBACK_HOST
    api_port: int = DEFAULT_LOOPBACK_PORT
    api_secret_key: str = Field(default="pyidm-local-dev-secret-key-256")

    model_config = SettingsConfigDict(env_prefix="PYIDM_", extra="ignore")

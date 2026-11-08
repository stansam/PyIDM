"""Unit tests for Native Messaging Host manifest generation and registry paths."""

import json
from pathlib import Path

from app.infrastructure.browser.registration import (
    FIREFOX_EXTENSION_ID,
    HOST_NAME,
    WINDOWS_REGISTRY_PATHS,
    create_host_manifests,
)


def test_create_host_manifests(tmp_path: Path) -> None:
    chromium_manifest, firefox_manifest = create_host_manifests(
        manifest_dir=tmp_path,
        python_exe=Path("C:/Python311/python.exe"),
    )

    assert chromium_manifest.exists()
    assert firefox_manifest.exists()

    # Verify Chromium manifest
    c_data = json.loads(chromium_manifest.read_text(encoding="utf-8"))
    assert c_data["name"] == HOST_NAME
    assert c_data["type"] == "stdio"
    assert "allowed_origins" in c_data
    assert "path" in c_data

    # Verify Firefox manifest
    f_data = json.loads(firefox_manifest.read_text(encoding="utf-8"))
    assert f_data["name"] == HOST_NAME
    assert f_data["type"] == "stdio"
    assert "allowed_extensions" in f_data
    assert FIREFOX_EXTENSION_ID in f_data["allowed_extensions"]


def test_windows_registry_paths_coverage() -> None:
    # Ensure all 5 target browsers are registered
    assert "chrome" in WINDOWS_REGISTRY_PATHS
    assert "edge" in WINDOWS_REGISTRY_PATHS
    assert "brave" in WINDOWS_REGISTRY_PATHS
    assert "opera" in WINDOWS_REGISTRY_PATHS
    assert "firefox" in WINDOWS_REGISTRY_PATHS

    # Verify Brave has its specific path rather than relying on Chrome fallback
    assert "BraveSoftware" in WINDOWS_REGISTRY_PATHS["brave"]


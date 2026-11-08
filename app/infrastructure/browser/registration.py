"""Automated registration of PyIDM Native Messaging Host across browsers."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("PyIDM.BrowserRegistration")

HOST_NAME = "com.pyidm.native.host"
FIREFOX_EXTENSION_ID = "pyidm@native.downloader"

# Windows HKCU Registry Paths for all supported browsers
WINDOWS_REGISTRY_PATHS: dict[str, str] = {
    "chrome": r"Software\Google\Chrome\NativeMessagingHosts",
    "edge": r"Software\Microsoft\Edge\NativeMessagingHosts",
    "brave": r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts",
    "opera": r"Software\Opera Software\NativeMessagingHosts",
    "firefox": r"Software\Mozilla\NativeMessagingHosts",
}

# Linux Native Messaging Paths
LINUX_USER_PATHS: dict[str, str] = {
    "chrome": "~/.config/google-chrome/NativeMessagingHosts",
    "edge": "~/.config/microsoft-edge/NativeMessagingHosts",
    "brave": "~/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts",
    "opera": "~/.config/opera/NativeMessagingHosts",
    "firefox": "~/.mozilla/native-messaging-hosts",
}


def get_default_manifest_dir() -> Path:
    """Return default directory storing native host manifests."""
    base = Path.home() / ".pyidm" / "native_messaging"
    base.mkdir(parents=True, exist_ok=True)
    return base


def create_host_manifests(
    manifest_dir: Path | None = None,
    python_exe: Path | None = None,
) -> tuple[Path, Path]:
    """Generate launcher scripts and JSON manifests for Chromium and Firefox.

    Returns (chromium_manifest_path, firefox_manifest_path).
    """
    target_dir = manifest_dir or get_default_manifest_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    py_executable = python_exe or Path(sys.executable)
    launcher_path: Path

    if sys.platform == "win32":
        launcher_path = target_dir / "pyidm_host.bat"
        # Create Windows launcher batch file
        launcher_content = (
            "@echo off\r\n"
            f'"{py_executable}" -m app.infrastructure.browser.host_cli %*\r\n'
        )
        launcher_path.write_text(launcher_content, encoding="utf-8")
    else:
        launcher_path = target_dir / "pyidm_host.sh"
        # Create Unix launcher script
        launcher_content = (
            "#!/bin/bash\n"
            f'exec "{py_executable}" -m app.infrastructure.browser.host_cli "$@"\n'
        )
        launcher_path.write_text(launcher_content, encoding="utf-8")
        launcher_path.chmod(0o755)

    # 1. Chromium Family Manifest (Chrome, Edge, Brave, Opera)
    chromium_manifest = {
        "name": HOST_NAME,
        "description": "PyIDM Native Messaging Host for Media Detection",
        "path": str(launcher_path.resolve()),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://*",
        ],
    }
    chromium_path = target_dir / f"{HOST_NAME}_chromium.json"
    chromium_path.write_text(
        json.dumps(chromium_manifest, indent=2), encoding="utf-8"
    )

    # 2. Firefox Manifest
    firefox_manifest = {
        "name": HOST_NAME,
        "description": "PyIDM Native Messaging Host for Media Detection",
        "path": str(launcher_path.resolve()),
        "type": "stdio",
        "allowed_extensions": [
            FIREFOX_EXTENSION_ID,
        ],
    }
    firefox_path = target_dir / f"{HOST_NAME}_firefox.json"
    firefox_path.write_text(
        json.dumps(firefox_manifest, indent=2), encoding="utf-8"
    )

    return chromium_path, firefox_path


def register_windows_registry(browser: str, manifest_path: Path) -> bool:
    """Register manifest path in Windows Registry under HKCU."""
    if sys.platform != "win32":
        return False

    import winreg

    sub_key = WINDOWS_REGISTRY_PATHS.get(browser.lower())
    if not sub_key:
        return False

    full_key = f"{sub_key}\\{HOST_NAME}"
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, full_key) as key:
            winreg.SetValueEx(
                key,
                "",  # (Default) value
                0,
                winreg.REG_SZ,
                str(manifest_path.resolve()),
            )
        return True
    except Exception as ex:
        logger.error("Failed to register registry key for %s: %s", browser, ex)
        return False


def unregister_windows_registry(browser: str) -> bool:
    """Remove manifest registration key from Windows Registry under HKCU."""
    if sys.platform != "win32":
        return False

    import winreg

    sub_key = WINDOWS_REGISTRY_PATHS.get(browser.lower())
    if not sub_key:
        return False

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_ALL_ACCESS
        ) as parent_key:
            winreg.DeleteKey(parent_key, HOST_NAME)
        return True
    except FileNotFoundError:
        return True
    except Exception as ex:
        logger.error("Failed to unregister registry key for %s: %s", browser, ex)
        return False


def register_all_browsers(manifest_dir: Path | None = None) -> dict[str, bool]:
    """Register PyIDM Native Messaging Host across Chrome, Edge, Brave, Opera, and Firefox."""
    chromium_path, firefox_path = create_host_manifests(manifest_dir)
    results: dict[str, bool] = {}

    if sys.platform == "win32":
        for browser in ("chrome", "edge", "brave", "opera"):
            results[browser] = register_windows_registry(browser, chromium_path)
        results["firefox"] = register_windows_registry("firefox", firefox_path)
    else:
        # Linux / Unix file copies
        for browser in ("chrome", "edge", "brave", "opera"):
            target_dir = Path(os.path.expanduser(LINUX_USER_PATHS[browser]))
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / f"{HOST_NAME}.json"
                target_file.write_text(
                    chromium_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
                results[browser] = True
            except Exception:
                results[browser] = False

        ff_dir = Path(os.path.expanduser(LINUX_USER_PATHS["firefox"]))
        try:
            ff_dir.mkdir(parents=True, exist_ok=True)
            ff_file = ff_dir / f"{HOST_NAME}.json"
            ff_file.write_text(
                firefox_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            results["firefox"] = True
        except Exception:
            results["firefox"] = False

    return results


def unregister_all_browsers() -> dict[str, bool]:
    """Unregister PyIDM Native Messaging Host from all supported browsers."""
    results: dict[str, bool] = {}
    if sys.platform == "win32":
        for browser in WINDOWS_REGISTRY_PATHS:
            results[browser] = unregister_windows_registry(browser)
    else:
        for browser, path_str in LINUX_USER_PATHS.items():
            f = Path(os.path.expanduser(path_str)) / f"{HOST_NAME}.json"
            if f.exists():
                try:
                    f.unlink()
                    results[browser] = True
                except Exception:
                    results[browser] = False
            else:
                results[browser] = True
    return results


def get_browser_status() -> dict[str, bool]:
    """Check whether Native Messaging registration is active for each browser."""
    status: dict[str, bool] = {}
    if sys.platform == "win32":
        import winreg

        for browser, sub_key in WINDOWS_REGISTRY_PATHS.items():
            full_key = f"{sub_key}\\{HOST_NAME}"
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, full_key, 0, winreg.KEY_READ
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    status[browser] = bool(val and Path(val).exists())
            except Exception:
                status[browser] = False
    else:
        for browser, path_str in LINUX_USER_PATHS.items():
            f = Path(os.path.expanduser(path_str)) / f"{HOST_NAME}.json"
            status[browser] = f.exists()
    return status

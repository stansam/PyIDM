"""Build script for PyIDM browser extensions compiling Chromium and Firefox bundles."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DIST_DIR = ROOT_DIR / "dist"
CHROMIUM_DIST = DIST_DIR / "chromium"
FIREFOX_DIST = DIST_DIR / "firefox"
CHROME_LEGACY_DIR = ROOT_DIR / "chrome"


def build_extensions() -> None:
    """Compile source files into dist/chromium, dist/firefox, and legacy chrome/ directories."""
    print("Building PyIDM cross-browser extension bundles...")

    # Clean dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    CHROMIUM_DIST.mkdir(parents=True, exist_ok=True)
    FIREFOX_DIST.mkdir(parents=True, exist_ok=True)
    CHROME_LEGACY_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Prepare combined background.js (sniffer + service_worker)
    sniffer_code = (SRC_DIR / "background" / "sniffer.js").read_text(encoding="utf-8")
    sw_code = (SRC_DIR / "background" / "service_worker.js").read_text(encoding="utf-8")
    combined_background = f"{sniffer_code}\n\n{sw_code}"

    # 2. Build Chromium Bundle (Chrome, Edge, Brave, Opera)
    (CHROMIUM_DIST / "background.js").write_text(combined_background, encoding="utf-8")
    shutil.copy2(SRC_DIR / "content" / "overlay.js", CHROMIUM_DIST / "overlay.js")
    shutil.copy2(SRC_DIR / "content" / "content.js", CHROMIUM_DIST / "content.js")
    shutil.copy2(SRC_DIR / "content" / "overlay.css", CHROMIUM_DIST / "overlay.css")
    shutil.copy2(SRC_DIR / "manifests" / "manifest.chromium.json", CHROMIUM_DIST / "manifest.json")

    # Mirror to legacy chrome/ directory
    (CHROME_LEGACY_DIR / "background.js").write_text(combined_background, encoding="utf-8")
    shutil.copy2(SRC_DIR / "content" / "overlay.js", CHROME_LEGACY_DIR / "overlay.js")
    shutil.copy2(SRC_DIR / "content" / "content.js", CHROME_LEGACY_DIR / "content.js")
    shutil.copy2(SRC_DIR / "content" / "overlay.css", CHROME_LEGACY_DIR / "overlay.css")
    shutil.copy2(SRC_DIR / "manifests" / "manifest.chromium.json", CHROME_LEGACY_DIR / "manifest.json")

    # 3. Build Firefox Bundle
    (FIREFOX_DIST / "background.js").write_text(combined_background, encoding="utf-8")
    shutil.copy2(SRC_DIR / "content" / "overlay.js", FIREFOX_DIST / "overlay.js")
    shutil.copy2(SRC_DIR / "content" / "content.js", FIREFOX_DIST / "content.js")
    shutil.copy2(SRC_DIR / "content" / "overlay.css", FIREFOX_DIST / "overlay.css")
    shutil.copy2(SRC_DIR / "manifests" / "manifest.firefox.json", FIREFOX_DIST / "manifest.json")

    print(f"✓ Chromium bundle created at: {CHROMIUM_DIST}")
    print(f"✓ Firefox bundle created at: {FIREFOX_DIST}")
    print(f"✓ Legacy Chrome bundle updated at: {CHROME_LEGACY_DIR}")


if __name__ == "__main__":
    build_extensions()


"""Helper script to register or unregister PyIDM Native Messaging Host across all browsers."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.infrastructure.browser.registration import (
    get_browser_status,
    register_all_browsers,
    unregister_all_browsers,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register PyIDM Native Messaging Host for Chrome, Edge, Brave, Opera, Firefox"
    )
    parser.add_argument("--unregister", action="store_true", help="Unregister from all browsers")
    parser.add_argument("--status", action="store_true", help="Display current registration status")
    args = parser.parse_args()

    if args.status:
        status = get_browser_status()
        print("PyIDM Native Messaging Registration Status:")
        for browser, is_active in status.items():
            state = "REGISTERED" if is_active else "NOT REGISTERED"
            print(f"  [{browser.upper()}]: {state}")
        return 0

    if args.unregister:
        print("Unregistering PyIDM from all browsers...")
        results = unregister_all_browsers()
        for browser, ok in results.items():
            print(f"  {browser}: {'OK' if ok else 'FAILED'}")
        return 0

    print("Registering PyIDM Native Messaging Host for all browsers...")
    results = register_all_browsers()
    for browser, ok in results.items():
        print(f"  {browser}: {'REGISTERED' if ok else 'FAILED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

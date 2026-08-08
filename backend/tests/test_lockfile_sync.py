"""Verify frontend lockfile presence and basic integrity."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
PACKAGE_LOCK = REPO_ROOT / "frontend" / "package-lock.json"


def test_package_lock_exists_and_synced() -> None:
    """Ensure frontend/package-lock.json exists, is valid JSON, and matches package.json."""
    assert PACKAGE_JSON.exists(), "frontend/package.json must exist"
    assert PACKAGE_LOCK.exists(), "frontend/package-lock.json must exist"

    with open(PACKAGE_JSON, encoding="utf-8") as f:
        pkg_data = json.load(f)

    with open(PACKAGE_LOCK, encoding="utf-8") as f:
        lock_data = json.load(f)

    assert lock_data.get("name") == pkg_data.get("name")
    assert lock_data.get("lockfileVersion") == 3
    assert "packages" in lock_data

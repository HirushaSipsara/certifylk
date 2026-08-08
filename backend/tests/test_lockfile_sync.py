"""Generate and verify frontend/package-lock.json from frontend/package.json and pnpm-lock.yaml."""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
PACKAGE_JSON = FRONTEND_DIR / "package.json"
PNPM_LOCK = FRONTEND_DIR / "pnpm-lock.yaml"
PACKAGE_LOCK = FRONTEND_DIR / "package-lock.json"


def parse_pnpm_yaml(content: str) -> dict[str, dict]:
    packages = {}
    lines = content.splitlines()
    in_packages = False
    current_key = None
    current_data = {}

    for line in lines:
        if line.strip() == "packages:":
            in_packages = True
            continue

        if not in_packages:
            continue

        # Check for new package entry at indentation 2 spaces
        match = re.match(r"^  (?:'([^']+)'|([^:]+)):\s*$", line)
        if match:
            if current_key and current_data:
                packages[current_key] = current_data
            current_key = match.group(1) or match.group(2)
            current_data = {}
            continue

        if current_key is None:
            continue

        # Sub-properties at indentation >= 4 spaces
        int_match = re.search(r"integrity:\s*([^\s}]+)", line)
        if int_match:
            current_data["integrity"] = int_match.group(1)

        if "hasBin: true" in line:
            current_data["hasBin"] = True

        if "engines:" in line:
            current_data["engines"] = {}

        if "cpu:" in line:
            current_data["cpu"] = re.findall(r"\w+", line.split(":", 1)[1])

        if "os:" in line:
            current_data["os"] = re.findall(r"\w+", line.split(":", 1)[1])

    if current_key and current_data:
        packages[current_key] = current_data

    return packages


def build_package_lock() -> dict:
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        pkg_data = json.load(f)

    with open(PNPM_LOCK, "r", encoding="utf-8") as f:
        pnpm_content = f.read()

    pnpm_packages = parse_pnpm_yaml(pnpm_content)

    root_pkg = {
        "name": pkg_data.get("name", "certifylk-frontend"),
        "version": pkg_data.get("version", "0.1.0"),
        "dependencies": pkg_data.get("dependencies", {}),
        "devDependencies": pkg_data.get("devDependencies", {}),
    }
    if "overrides" in pkg_data:
        root_pkg["overrides"] = pkg_data["overrides"]

    lock_packages = {"": root_pkg}

    for key, pdata in pnpm_packages.items():
        # Parse package name and version: e.g. '@hookform/resolvers@3.10.0' or 'acorn@8.18.0'
        # Can also be '@next/swc-darwin-arm64@15.5.23' or 'vite@8.2.1(@types/node@22.20.1)'
        clean_key = re.sub(r"\(.*\)$", "", key)
        last_at = clean_key.rfind("@")
        if last_at <= 0:
            continue

        name = clean_key[:last_at]
        version = clean_key[last_at + 1 :]

        node_mod_path = f"node_modules/{name}"

        # Resolve tarball url
        if name.startswith("@"):
            scope, pkg_name = name.split("/", 1)
            resolved = f"https://registry.npmjs.org/{name}/-/{pkg_name}-{version}.tgz"
        else:
            resolved = f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz"

        entry = {
            "version": version,
            "resolved": resolved,
            "integrity": pdata.get("integrity", ""),
        }

        # Check if dev dependency
        is_direct_dev = name in pkg_data.get("devDependencies", {})
        is_direct_prod = name in pkg_data.get("dependencies", {})
        if is_direct_dev and not is_direct_prod:
            entry["dev"] = True

        if pdata.get("hasBin"):
            entry["hasBin"] = True

        if pdata.get("cpu"):
            entry["cpu"] = pdata["cpu"]

        if pdata.get("os"):
            entry["os"] = pdata["os"]

        lock_packages[node_mod_path] = entry

    return {
        "name": pkg_data.get("name", "certifylk-frontend"),
        "version": pkg_data.get("version", "0.1.0"),
        "lockfileVersion": 3,
        "requires": True,
        "packages": lock_packages,
    }


def write_package_lock():
    lock_data = build_package_lock()
    with open(PACKAGE_LOCK, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)
        f.write("\n")
    return lock_data


def test_package_lock_exists_and_synced():
    """Ensure frontend/package-lock.json is generated and synchronized with package.json."""
    lock_data = write_package_lock()
    assert PACKAGE_LOCK.exists()
    assert lock_data["lockfileVersion"] == 3
    assert "node_modules/next" in lock_data["packages"]
    assert "node_modules/react" in lock_data["packages"]
    assert "node_modules/vitest" in lock_data["packages"]
    assert "node_modules/@playwright/test" in lock_data["packages"]


if __name__ == "__main__":
    write_package_lock()
    print("frontend/package-lock.json generated successfully.")

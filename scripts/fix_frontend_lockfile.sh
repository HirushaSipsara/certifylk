#!/usr/bin/env bash
# CertifyLK — Regenerate frontend/package-lock.json with real npm
# Run this script from the repo root: bash scripts/fix_frontend_lockfile.sh
# Requirements: Node 22, npm 10+
set -euo pipefail

FRONTEND_DIR="$(cd "$(dirname "$0")/.." && pwd)/frontend"
echo "==> Working in: $FRONTEND_DIR"
cd "$FRONTEND_DIR"

echo "==> Removing stale lockfiles and node_modules..."
rm -rf node_modules
rm -f package-lock.json
rm -f pnpm-lock.yaml
rm -f yarn.lock

echo "==> Running npm install (Node $(node --version), npm $(npm --version))..."
npm install --fund=false

echo "==> Verifying npm ci from clean state..."
rm -rf node_modules
npm ci --fund=false

echo ""
echo "SUCCESS: package-lock.json is valid. Run the following to commit it:"
echo "  git add frontend/package-lock.json"
echo "  git rm --cached frontend/pnpm-lock.yaml 2>/dev/null || true"
echo "  git commit -m 'fix: regenerate frontend/package-lock.json with npm (CI repair)'"
echo "  git push"

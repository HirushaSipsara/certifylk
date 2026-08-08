# CertifyLK — Regenerate frontend/package-lock.json with real npm
# Run this from the repo root in PowerShell:
#   .\scripts\fix_frontend_lockfile.ps1
# Requirements: Node 22, npm 10+
$ErrorActionPreference = "Stop"
$FrontendDir = Join-Path $PSScriptRoot ".." "frontend"
Set-Location $FrontendDir

Write-Host "==> Working in: $(Get-Location)"

Write-Host "==> Removing stale lockfiles and node_modules..."
Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
Remove-Item -Force "package-lock.json" -ErrorAction SilentlyContinue
Remove-Item -Force "pnpm-lock.yaml" -ErrorAction SilentlyContinue
Remove-Item -Force "yarn.lock" -ErrorAction SilentlyContinue

Write-Host "==> Running npm install..."
node --version
npm --version
npm install --fund=false

Write-Host "==> Verifying npm ci from clean state..."
Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
npm ci --fund=false

Write-Host ""
Write-Host "SUCCESS: package-lock.json is valid. Now commit it:"
Write-Host '  git add frontend/package-lock.json'
Write-Host '  git rm --cached frontend/pnpm-lock.yaml 2>$null; git commit -m "fix: regenerate frontend/package-lock.json with npm (CI repair)"; git push'

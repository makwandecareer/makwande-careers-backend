param([string]$ProjectRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"

$target = Join-Path $ProjectRoot "app\billing\config.py"
$source = Join-Path $PSScriptRoot "config.py"

if (-not (Test-Path (Join-Path $ProjectRoot "app\main.py"))) {
    throw "Run this script from the backend repository root."
}

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    throw ".env was not found in the backend repository root."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $target "$target.before-env-fix-$stamp" -Force
Copy-Item $source $target -Force

Write-Host "Billing .env loading fixed." -ForegroundColor Green
Write-Host "Now run:"
Write-Host "python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

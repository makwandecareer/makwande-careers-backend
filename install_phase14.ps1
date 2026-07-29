param(
  [string]$BackendRoot = "E:\Makwande_Careers_Backend\makwande-Careers-backend",
  [string]$FrontendRoot = "E:\Makwande_Careers_Dashboard_1430"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$BackendServices = Join-Path $BackendRoot "app\services"
$FrontendComponents = Join-Path $FrontendRoot "components\cv-builder"

if (-not (Test-Path $BackendServices)) {
  throw "Backend services folder not found: $BackendServices"
}
if (-not (Test-Path $FrontendComponents)) {
  New-Item -ItemType Directory -Force -Path $FrontendComponents | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $BackendRoot "phase14_backup_$timestamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$files = @(
  "cv_builder_v4_1.py",
  "resume_formalization_engine.py",
  "resume_skills_engine.py",
  "resume_intelligence_engine.py",
  "resume_phase14_engine.py",
  "resume_recommendation_engine.py"
)

foreach ($file in $files) {
  $target = Join-Path $BackendServices $file
  if (Test-Path $target) {
    Copy-Item $target (Join-Path $backup $file) -Force
  }
  Copy-Item (Join-Path $PackageRoot "app\services\$file") $target -Force
}

Copy-Item (Join-Path $PackageRoot "components\cv-builder\ResumeRecommendationsPopup.tsx") `
  (Join-Path $FrontendComponents "ResumeRecommendationsPopup.tsx") -Force
Copy-Item (Join-Path $PackageRoot "components\cv-builder\ResumeIntelligenceDashboard.tsx") `
  (Join-Path $FrontendComponents "ResumeIntelligenceDashboard.tsx") -Force

Write-Host "Phase 14 files installed successfully." -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host "Run backend validation: python -m compileall app"
Write-Host "Run frontend validation: npm run build"

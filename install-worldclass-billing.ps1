param([string]$ProjectRoot=(Get-Location).Path)
$ErrorActionPreference="Stop"

$mainPath=Join-Path $ProjectRoot "app\main.py"
$requirementsPath=Join-Path $ProjectRoot "requirements.txt"
$source=Join-Path $PSScriptRoot "_payment_patch"

if(-not(Test-Path $mainPath)){
  throw "Run this installer from the backend repository root containing app\main.py"
}

$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $mainPath "$mainPath.before-worldclass-billing-$stamp" -Force

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "app\billing") | Out-Null
Copy-Item (Join-Path $source "app\billing\*") (Join-Path $ProjectRoot "app\billing") -Force
Copy-Item (Join-Path $source "migrations\001_worldclass_billing.sql") (Join-Path $ProjectRoot "migrations\001_worldclass_billing.sql") -Force
Copy-Item (Join-Path $source ".env.billing.example") (Join-Path $ProjectRoot ".env.billing.example") -Force
Copy-Item (Join-Path $source "requirements-billing.txt") (Join-Path $ProjectRoot "requirements-billing.txt") -Force

$main=Get-Content $mainPath -Raw
if($main -notmatch 'from app\.billing\.routes import router as billing_router'){
  $main="from app.billing.routes import router as billing_router`nfrom app.billing.startup import initialise_billing`n"+$main
}
if($main -notmatch 'app\.include_router\(billing_router'){
  $main+="`napp.include_router(billing_router, prefix=`"/api`")`n"
}
if($main -notmatch 'initialise_billing\(\)'){
  $main+="`ninitialise_billing()`n"
}
Set-Content $mainPath $main -Encoding utf8

if(Test-Path $requirementsPath){
  $existing=Get-Content $requirementsPath -Raw
  foreach($line in Get-Content (Join-Path $source "requirements-billing.txt")){
    $name=($line -split '[<>=\[]')[0]
    if($line.Trim() -and $existing -notmatch "(?m)^$([regex]::Escape($name))"){
      Add-Content $requirementsPath $line
    }
  }
}

Write-Host ""
Write-Host "World-class billing backend installed." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  python -m pip install -r requirements.txt"
Write-Host "  copy values from .env.billing.example into .env"
Write-Host "  python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

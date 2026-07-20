param([string]$ProjectRoot=(Get-Location).Path)
$ErrorActionPreference="Stop"
$main=Join-Path $ProjectRoot "app\main.py"
$req=Join-Path $ProjectRoot "requirements.txt"
if(-not(Test-Path $main)){throw "Run from backend repository root containing app\main.py"}
$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $main "$main.before-openai-paystack-$stamp" -Force
Copy-Item "$PSScriptRoot\_backend_patch\app\core\integration_settings.py" "$ProjectRoot\app\core\integration_settings.py" -Force
Copy-Item "$PSScriptRoot\_backend_patch\app\services\*" "$ProjectRoot\app\services" -Force
Copy-Item "$PSScriptRoot\_backend_patch\app\routes\*" "$ProjectRoot\app\routes" -Force
Copy-Item "$PSScriptRoot\_backend_patch\.env.openai-paystack.example" "$ProjectRoot\.env.openai-paystack.example" -Force
Copy-Item "$PSScriptRoot\_backend_patch\requirements-openai-paystack.txt" "$ProjectRoot\requirements-openai-paystack.txt" -Force
$m=Get-Content $main -Raw
if($m -notmatch 'from app\.routes import billing, openai_career'){$m="from app.routes import billing, openai_career`nfrom app.services.integration_startup import initialise_openai_and_billing`n"+$m}
if($m -notmatch 'app\.include_router\(billing\.router'){$m+="`napp.include_router(billing.router, prefix=`"/api`")`napp.include_router(openai_career.router, prefix=`"/api`")`n"}
if($m -notmatch 'initialise_openai_and_billing\(\)'){$m+="`ninitialise_openai_and_billing()`n"}
Set-Content $main $m -Encoding utf8
if(Test-Path $req){
  foreach($line in Get-Content "$PSScriptRoot\_backend_patch\requirements-openai-paystack.txt"){
    $name=($line -split '[<>=\[]')[0]
    if($line.Trim() -and (Get-Content $req -Raw) -notmatch "(?m)^$([regex]::Escape($name))"){Add-Content $req $line}
  }
}
Write-Host "OpenAI and Paystack modules installed." -ForegroundColor Green

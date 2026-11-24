param([int]$Port=8797,[string]$Ledger="$env:USERPROFILE\MYRIAD\evolution-mesh.sqlite3")
$ErrorActionPreference='Stop'
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
  if (!(Test-Path (Split-Path $Ledger))) { New-Item -ItemType Directory -Force -Path (Split-Path $Ledger) | Out-Null }
  python scripts/evolution_scheduler.py --db $Ledger init
  Write-Host "MYRIAD Ω website: http://127.0.0.1:$Port"
  Write-Host 'This is a research-only, local read-only observatory.'
  python scripts/evolution_api.py --port $Port --ledger $Ledger
} finally { Pop-Location }

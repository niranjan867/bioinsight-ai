$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $ProjectRoot "frontend"
if (-not (Test-Path -LiteralPath (Join-Path $FrontendPath "node_modules"))) { throw "Frontend dependencies not found. Run scripts/setup.ps1 first." }
Push-Location $FrontendPath
try { npm run dev } finally { Pop-Location }

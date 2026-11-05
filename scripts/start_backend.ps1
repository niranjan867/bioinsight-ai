$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Backend environment not found. Run scripts/setup.ps1 first." }
if (-not (Test-Path -LiteralPath (Join-Path $BackendPath ".env"))) { throw "backend/.env is missing. Run scripts/configure_db.py or scripts/setup.ps1 first." }
Push-Location $BackendPath
try { & $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload } finally { Pop-Location }

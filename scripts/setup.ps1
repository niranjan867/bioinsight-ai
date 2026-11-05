param([switch]$SkipDatabaseConfiguration)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot "check_environment.ps1")
if ($LASTEXITCODE -ne 0) { throw "Install the missing prerequisites shown above, then run setup.ps1 again." }

$BackendPath = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating backend virtual environment..."
    & py -3.12 -m venv (Join-Path $BackendPath ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python virtual environment." }
}
Write-Host "Installing backend dependencies..."
Push-Location $BackendPath
try {
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }
    & $VenvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Could not install backend requirements." }
} finally { Pop-Location }

Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $ProjectRoot "frontend")
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "Could not install frontend dependencies." }
} finally { Pop-Location }

$BackendEnv = Join-Path $BackendPath ".env"
$FrontendEnv = Join-Path $ProjectRoot "frontend\.env.local"
if ($SkipDatabaseConfiguration -and -not (Test-Path -LiteralPath $BackendEnv)) {
    Copy-Item -LiteralPath (Join-Path $BackendPath ".env.example") -Destination $BackendEnv
    Write-Host "Created backend/.env from the safe template. Configure its database before starting the API."
}
if (-not (Test-Path -LiteralPath $FrontendEnv)) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "frontend\.env.example") -Destination $FrontendEnv
    Write-Host "Created frontend/.env.local from the safe template."
}

if (-not $SkipDatabaseConfiguration) {
    Write-Host "The database helper uses your own PostgreSQL role and password and never drops a database."
    & $VenvPython (Join-Path $ProjectRoot "scripts\configure_db.py")
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL configuration did not complete. See the message above." }
    Push-Location $BackendPath
    try {
        & $VenvPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Check backend/.env and PostgreSQL permissions." }
    } finally { Pop-Location }
}

Write-Host "Setup finished. Run scripts/start_all.ps1 to start both local services." -ForegroundColor Green

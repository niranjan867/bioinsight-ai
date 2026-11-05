$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Problems = [System.Collections.Generic.List[string]]::new()

Write-Host "BioInsight AI environment check" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"

if (Get-Command git -ErrorAction SilentlyContinue) { git --version } else { $Problems.Add("Git is not installed or not on PATH.") }

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    & py -3.12 --version
    if ($LASTEXITCODE -ne 0) { $Problems.Add("Python 3.12 was not found. Install Python 3.12 and enable the Python Launcher.") }
} else { $Problems.Add("Python Launcher 'py' is missing. Install Python 3.12 with the launcher enabled.") }

if (Get-Command node -ErrorAction SilentlyContinue) {
    node --version
    npm --version
} else { $Problems.Add("Node.js and npm are not installed or not on PATH.") }

$PgIsReady = Get-Command pg_isready -ErrorAction SilentlyContinue
if ($PgIsReady) {
    & pg_isready -h 127.0.0.1 -p 5432
    if ($LASTEXITCODE -ne 0) { Write-Warning "PostgreSQL is installed but is not accepting connections on 127.0.0.1:5432." }
} elseif (Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue) {
    Write-Host "PostgreSQL port 5432 is accepting TCP connections. Credentials are not checked by this test."
} else {
    Write-Warning "No PostgreSQL service was detected on 127.0.0.1:5432. Install/start PostgreSQL before database setup."
}

if ($Problems.Count -gt 0) {
    Write-Host "Environment prerequisites are missing:" -ForegroundColor Yellow
    $Problems | ForEach-Object { Write-Host " - $_" }
    exit 1
}
Write-Host "Required command-line prerequisites found." -ForegroundColor Green

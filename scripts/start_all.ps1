$ErrorActionPreference = "Stop"
$BackendScript = Join-Path $PSScriptRoot "start_backend.ps1"
$FrontendScript = Join-Path $PSScriptRoot "start_frontend.ps1"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"))) { throw "Run scripts/setup.ps1 before starting BioInsight AI." }

Start-Process -FilePath "powershell.exe" -WorkingDirectory $ProjectRoot -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $BackendScript))
Start-Process -FilePath "powershell.exe" -WorkingDirectory $ProjectRoot -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $FrontendScript))
Write-Host "Backend:  http://127.0.0.1:8000 (docs: /docs)"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Close the two PowerShell windows to stop the services."

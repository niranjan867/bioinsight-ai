# Windows local installation

This is a source-based local setup guide. BioInsight AI has no EXE/MSI installer.

## Install prerequisites

Install Git, Python 3.12 with the Python Launcher, Node.js 20.9+, and PostgreSQL 18. `scripts/check_environment.ps1` checks command availability and whether the default PostgreSQL port accepts TCP connections.

## Clone and configure

```powershell
git clone https://github.com/niranjan867/bioinsight-ai.git
Set-Location .\bioinsight-ai
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Setup creates the Python virtual environment, installs dependencies with pip and `npm ci`, and asks for a dedicated application role/database configuration. If PostgreSQL administrator credentials are entered, the helper only creates the named role/database and grants schema access; it never drops a database. Existing role password rotation and replacement of `backend/.env` each require explicit confirmation.

Configuration files are private and local:

- `backend/.env` — PostgreSQL URL, generated JWT secret placeholder/config, optional `NCBI_EMAIL`.
- `frontend/.env.local` — local FastAPI URL.

## Run

```powershell
.\scripts\start_all.ps1
```

Or run the backend and frontend scripts in separate PowerShell windows. Open:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

See [FRIEND_SETUP_GUIDE.md](FRIEND_SETUP_GUIDE.md) for the full clone-and-run checklist.

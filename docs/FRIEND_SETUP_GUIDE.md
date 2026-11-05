# Setup BioInsight AI on another Windows PC

This guide uses a clean clone and your own local PostgreSQL credentials. You do not need access to the original developer's computer, database, `.env` files, or credentials. There is no Windows installer.

## 1. Install prerequisites

Install:

1. Git for Windows.
2. Python 3.12 and enable the Python Launcher (`py`).
3. Node.js 20.9 or later (npm is included).
4. PostgreSQL 18.

Open a new PowerShell window and check:

```powershell
git --version
py -3.12 --version
node --version
npm --version
```

## 2. Clone the repository

```powershell
git clone https://github.com/niranjan867/bioinsight-ai.git
Set-Location .\bioinsight-ai
```

You can clone into any folder; the scripts resolve paths relative to the repository.

## 3. Run guided setup

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

The script creates `backend/.venv`, installs Python and Node dependencies, and opens a prompt to configure a dedicated database and application role. Choose your own database name, role, and password. If you provide PostgreSQL administrator credentials, the helper can create that role/database. It never drops databases and confirms before changing an existing role password. A random JWT secret is written to your ignored local `backend/.env`.

If you already have an application role and database, enter the credentials to verify them. If setup detects an existing `.env`, it asks before replacing it; answer `N` to preserve it.

For optional NCBI BLAST, enter a contact email. Leave blank to keep BLAST disabled; gene/protein/sequence analysis still works.

## 4. Start the application

```powershell
.\scripts\start_all.ps1
```

This opens one PowerShell window for each service. Close those windows to stop them. Visit:

- BioInsight AI: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## 5. Manual start

You can start services separately:

```powershell
.\scripts\start_backend.ps1
```

```powershell
.\scripts\start_frontend.ps1
```

## Troubleshooting

- Run `powershell -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1` to check prerequisites.
- If Python is missing, install Python 3.12 and enable the `py` launcher.
- If database connection fails, confirm PostgreSQL is running, then rerun `python .\scripts\configure_db.py` and check host, port, role, database, and password.
- If the UI says the backend is unavailable, verify the backend at `http://127.0.0.1:8000/health` and confirm `frontend/.env.local` uses that URL.
- External gene/protein services require internet access. NCBI BLAST also needs `NCBI_EMAIL`.
- Never share or commit your `.env` files, passwords, private sequences, or local research reports.

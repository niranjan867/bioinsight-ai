# Troubleshooting

## PowerShell blocks scripts

Run the requested script with a process-scoped bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

## Python 3.12 is not found

Install Python 3.12 and its Python Launcher, then open a new PowerShell window and check `py -3.12 --version`. Do not copy a virtual environment from another computer; rerun setup to create a local one.

## PostgreSQL connection fails

Check that the PostgreSQL service is running and listening at the host/port in `backend/.env`. Verify the application role, database, and password using `scripts/configure_db.py`. The helper does not drop databases. Check the PostgreSQL server log and `pg_hba.conf` if credentials are rejected.

## Migration errors

From the `backend` folder, run `.venv\Scripts\python.exe -m alembic current` and `.venv\Scripts\python.exe -m alembic upgrade head`. Confirm the application role can create objects in schema `public`.

## Frontend cannot reach the API

Check that the backend is running at `http://127.0.0.1:8000`, then check `frontend/.env.local` has `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`. Restart the frontend after changing environment variables.

## Gene/protein lookup fails

These lookups contact external scientific services. Check internet connectivity and retry later. The UI should report a source error rather than return invented results.

## NCBI BLAST is unavailable

Set `NCBI_EMAIL` in the private `backend/.env`, ensure the selected query type matches its BLAST database, and allow time for NCBI to process the RID. Local job status is lost when the backend restarts.

## Port already in use

Stop the existing service using port 3000 or 8000, or configure a different port deliberately and update frontend API/CORS settings to match.

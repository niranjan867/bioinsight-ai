# Security and privacy

## Current safeguards

- Local environment files are excluded by `.gitignore`; templates contain placeholders only.
- `scripts/configure_db.py` requests database credentials interactively, never prints passwords, creates only the named application role/database, and confirms before rotating an existing role password or replacing an existing backend environment file.
- PostgreSQL is reached through SQLAlchemy and `psycopg`; user input is not interpolated into SQL identifiers/values in the setup utility.
- The API health checks return masked database failure messages. CORS allows the configured frontend origin.
- Upload size and sequence length limits are enforced. Sequence characters are validated against explicit alphabets.
- NCBI BLAST uses a fixed upstream URL, an allowlist of databases, a contact address, a request throttle, and a bounded, expiring in-memory job map.

## Important limitations

- User registration, authentication, authorization, and project ownership are not implemented. Do not expose the service on a public or shared network or store private multi-user research data.
- Local development defaults enable debug mode and a placeholder signing secret. The placeholder is not suitable for production; authentication is not yet wired to these values.
- BLAST sequences are sent to NCBI. Only submit data appropriate for that external service.
- External API requests can disclose query terms/identifiers to those providers.
- The application does not provide regulated clinical decision support.

## Git and local data

Never commit `.env`, `.env.local`, passwords, API keys, JWT secrets, local database dumps, backups, uploaded files, private sequences, or generated reports. Before any release, inspect `git status`, tracked files, and commit diffs. Rotate a secret if it was ever committed.

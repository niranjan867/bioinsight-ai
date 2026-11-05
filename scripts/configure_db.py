"""Interactively create a dedicated local PostgreSQL role/database and backend env file."""

import getpass
import secrets
import sys
from pathlib import Path
from urllib.parse import quote_plus

import psycopg
from psycopg import sql

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_ENV_PATH = ROOT_DIR / "backend" / ".env"


def connect_as_app(host: str, port: int, database: str, role: str, password: str) -> bool:
    try:
        with psycopg.connect(
            host=host, port=port, dbname=database, user=role, password=password,
            connect_timeout=4,
        ) as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False


def configure_database(
    host: str, port: int, database: str, role: str, password: str,
    admin_role: str, admin_password: str,
) -> None:
    """Create the app role/database when absent; never drop or take ownership of existing data."""
    with psycopg.connect(
        host=host, port=port, dbname="postgres", user=admin_role,
        password=admin_password, autocommit=True, connect_timeout=4,
    ) as connection:
        role_exists = connection.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)
        ).fetchone()
        if role_exists:
            rotate = input(f"Role '{role}' exists. Set its password to the app password you entered? (y/N): ").strip().lower()
            if rotate != "y":
                raise RuntimeError("Existing database role was left unchanged.")
            connection.execute(
                sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
        else:
            connection.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )

        db_exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
        ).fetchone()
        if db_exists:
            connection.execute(
                sql.SQL("GRANT CONNECT, CREATE ON DATABASE {} TO {}").format(
                    sql.Identifier(database), sql.Identifier(role)
                )
            )
        else:
            connection.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(role)
                )
            )

    with psycopg.connect(
        host=host, port=port, dbname=database, user=admin_role,
        password=admin_password, autocommit=True, connect_timeout=4,
    ) as connection:
        connection.execute(
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(role))
        )


def write_backend_env(host: str, port: int, database: str, role: str, password: str, email: str) -> None:
    encoded_password = quote_plus(password)
    content = f"""# BioInsight AI local backend settings. This file is private and ignored by Git.
APP_NAME=BioInsight AI
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql+psycopg://{quote_plus(role)}:{encoded_password}@{host}:{port}/{quote_plus(database)}
JWT_SECRET_KEY={secrets.token_urlsafe(48)}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STORAGE_PATH=../storage
MAX_UPLOAD_SIZE_MB=25
FRONTEND_URL=http://localhost:3000
NCBI_EMAIL={email}
NCBI_TOOL=BioInsightAI
"""
    BACKEND_ENV_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    print("BioInsight AI local PostgreSQL configuration")
    print("This creates or configures only the role and database you name. It never drops a database.")
    if BACKEND_ENV_PATH.exists():
        confirmation = input("backend/.env already exists. Replace its settings and generated JWT secret? (y/N): ").strip().lower()
        if confirmation != "y":
            print("Existing environment file preserved.")
            return 0

    host = input("PostgreSQL host [127.0.0.1]: ").strip() or "127.0.0.1"
    port_text = input("PostgreSQL port [5432]: ").strip() or "5432"
    database = input("BioInsight database name [bioinsight_db]: ").strip() or "bioinsight_db"
    role = input("BioInsight application role [bioinsight_app]: ").strip() or "bioinsight_app"
    try:
        port = int(port_text)
    except ValueError:
        print("Port must be a number.")
        return 1
    if not database.replace("_", "").isalnum() or not role.replace("_", "").isalnum():
        print("Use letters, numbers, and underscores for the database and role names.")
        return 1

    password = getpass.getpass("New application role password (leave blank to generate one): ")
    if not password:
        password = secrets.token_urlsafe(32)
        print("A random app password was generated and will be stored only in ignored backend/.env.")
    email = input("Contact email for optional NCBI BLAST [leave blank to disable BLAST]: ").strip()

    if not connect_as_app(host, port, database, role, password):
        admin_role = input("PostgreSQL administrator role [postgres]: ").strip() or "postgres"
        admin_password = getpass.getpass("Password for that PostgreSQL administrator: ")
        try:
            configure_database(host, port, database, role, password, admin_role, admin_password)
        except (psycopg.Error, RuntimeError) as exc:
            print(f"Could not configure PostgreSQL ({type(exc).__name__}). No database was dropped.")
            return 1
        if not connect_as_app(host, port, database, role, password):
            print("The application role could not connect. Check PostgreSQL host, port, role grants, and pg_hba.conf.")
            return 1

    write_backend_env(host, port, database, role, password, email)
    print("Database connection verified. Private backend/.env created with a new JWT secret.")
    print("Next: run scripts/setup.ps1, or install dependencies and run `alembic upgrade head` from backend/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

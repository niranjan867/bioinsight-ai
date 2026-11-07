import pytest
from app.core.config import Settings


def test_settings_load_defaults():
    """Verify that settings load with correct defaults and valid structure."""
    settings = Settings()
    assert settings.APP_NAME == "BioInsight AI"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES >= 1
    assert settings.MAX_UPLOAD_SIZE_MB >= 1
    assert settings.FRONTEND_URL.startswith("http")


def test_settings_storage_path_resolution():
    """Verify that the resolved storage path points to a valid Path object."""
    settings = Settings(STORAGE_PATH="../storage")
    resolved = settings.resolved_storage_path
    assert resolved.name == "storage"


def test_database_url_normalization_postgres_prefix():
    """Verify standard 'postgres://' scheme normalizes to 'postgresql+psycopg://'."""
    settings = Settings(DATABASE_URL="postgres://app_user:secret_pwd@db.host.internal:5432/bioinsight")
    assert settings.DATABASE_URL == "postgresql+psycopg://app_user:secret_pwd@db.host.internal:5432/bioinsight"


def test_database_url_normalization_postgresql_prefix():
    """Verify 'postgresql://' scheme normalizes to 'postgresql+psycopg://'."""
    settings = Settings(DATABASE_URL="postgresql://neon_user:neon_key@ep-cool.us-east-2.aws.neon.tech/neondb?sslmode=require")
    assert settings.DATABASE_URL == "postgresql+psycopg://neon_user:neon_key@ep-cool.us-east-2.aws.neon.tech/neondb?sslmode=require"


def test_database_url_already_normalized():
    """Verify already-correct 'postgresql+psycopg://' scheme is preserved unchanged."""
    url = "postgresql+psycopg://render_user:pass123@dpg-host:5432/db_prod"
    settings = Settings(DATABASE_URL=url)
    assert settings.DATABASE_URL == url


def test_database_url_sqlite_supported():
    """Verify 'sqlite://' formats are preserved for testing and in-memory workflows."""
    mem_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    assert mem_settings.DATABASE_URL == "sqlite:///:memory:"

    file_settings = Settings(DATABASE_URL="sqlite:///test.db")
    assert file_settings.DATABASE_URL == "sqlite:///test.db"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "mysql://user:pass@localhost:3306/db",
        "oracle://user:pass@localhost:1521/db",
        "mongodb://localhost:27017/db",
        "redis://localhost:6379/0",
        "http://localhost:5432/db",
        "invalid-scheme",
    ],
)
def test_database_url_rejects_unsupported_schemes(invalid_url: str):
    """Verify that unsupported database URL schemes are rejected with ValueError without leaking credentials."""
    with pytest.raises(ValueError, match="DATABASE_URL must be a PostgreSQL URL"):
        Settings(DATABASE_URL=invalid_url)

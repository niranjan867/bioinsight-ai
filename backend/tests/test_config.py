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


def test_settings_database_url_validation():
    """Verify that invalid database URL schemes raise ValueError."""
    with pytest.raises(ValueError, match="DATABASE_URL must start with"):
        Settings(DATABASE_URL="mysql://user:pass@localhost/db")

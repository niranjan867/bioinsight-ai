from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment and backend/.env."""

    APP_NAME: str = Field(default="BioInsight AI", description="Application name")
    APP_ENV: str = Field(default="development", description="Environment: development, test, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")

    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://bioinsight_app:change_me@127.0.0.1:5432/bioinsight_db",
        description="SQLAlchemy database URL with psycopg driver",
    )

    # Security & Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-this-jwt-secret-key-in-your-local-env-file",
        description="Cryptographic secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="Access token expiration in minutes")
    NCBI_EMAIL: str = Field(default="", description="Contact email required by NCBI BLAST usage policy")
    NCBI_TOOL: str = Field(default="BioInsightAI", description="Application identifier sent to NCBI")

    # Storage & Uploads
    STORAGE_PATH: str = Field(default="../storage", description="Path to storage directory")
    MAX_UPLOAD_SIZE_MB: int = Field(default=25, ge=1, le=500, description="Max upload size in MB")

    # Client Origin
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Allowed CORS origin for frontend")

    model_config = SettingsConfigDict(
        env_file=(
            BACKEND_DIR / ".env",
            Path(".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        url = v.strip()
        # Normalize standard cloud PostgreSQL prefixes to psycopg3 driver dialect
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]

        if not url.startswith(("postgresql+psycopg://", "sqlite://")):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL URL (normalized to 'postgresql+psycopg://') or SQLite URL ('sqlite://')"
            )
        return url

    @property
    def resolved_storage_path(self) -> Path:
        """Resolve storage path relative to project root or absolute path."""
        p = Path(self.STORAGE_PATH)
        if p.is_absolute():
            return p
        return (BACKEND_DIR / p).resolve()


# Reusable singleton instance
settings = Settings()

from app.database.session import get_db
from app.main import app, resolve_cors_origins
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


def test_root_health_endpoint(client: TestClient):
    """Test root /health endpoint returns healthy status and metadata."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "BioInsight AI"
    assert "version" in data
    assert "environment" in data


def test_api_v1_health_endpoint(client: TestClient):
    """Test /api/v1/health endpoint returns healthy status and API version."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"
    assert data["application"] == "BioInsight AI"


def test_database_health_success(client: TestClient):
    """Test /api/v1/health/db and /health/db return 200 when database responds."""
    for path in ["/api/v1/health/db", "/health/db"]:
        response = client.get(path)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


def test_database_health_failure_masks_internals(client: TestClient):
    """Test that database connection failure returns 503 and masks all sensitive details."""
    from unittest.mock import MagicMock

    from sqlalchemy.orm import Session

    mock_failing_session = MagicMock(spec=Session)
    mock_failing_session.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("FATAL: password authentication failed")
    )

    def failing_get_db():
        yield mock_failing_session

    app.dependency_overrides[get_db] = failing_get_db

    try:
        for path in ["/api/v1/health/db", "/health/db"]:
            response = client.get(path)
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert "detail" in data
            detail = data["detail"]
            assert detail["status"] == "unhealthy"
            assert detail["database"] == "unavailable"

            # Strict check: Never leak internal error messages, passwords, or connection strings
            response_text = response.text.lower()
            assert "password" not in response_text
            assert "authentication failed" not in response_text
            assert "postgresql" not in response_text
    finally:
        app.dependency_overrides.clear()


def test_cors_preflight(client: TestClient):
    """Verify CORS preflight headers restrict to configured frontend origin."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_resolve_cors_origins_multiple_and_whitespace():
    """Verify comma-separated origins are trimmed and empty entries ignored."""
    raw = " https://bioinsight.vercel.app , , https://bioinsight-git-master.vercel.app , "
    origins = resolve_cors_origins(raw, app_env="production")
    assert origins == [
        "https://bioinsight.vercel.app",
        "https://bioinsight-git-master.vercel.app",
    ]


def test_resolve_cors_origins_wildcard_rejection():
    """Verify wildcard '*' origins are stripped to prevent insecure credentialed CORS."""
    raw = "*, https://bioinsight.vercel.app"
    origins = resolve_cors_origins(raw, app_env="production")
    assert "*" not in origins
    assert origins == ["https://bioinsight.vercel.app"]


def test_resolve_cors_origins_development_vs_production():
    """Verify development mode appends local origins while production remains strictly isolated."""
    dev_origins = resolve_cors_origins("https://preview.vercel.app", app_env="development")
    assert "http://localhost:3000" in dev_origins
    assert "http://127.0.0.1:3000" in dev_origins
    assert "https://preview.vercel.app" in dev_origins

    prod_origins = resolve_cors_origins("https://preview.vercel.app", app_env="production")
    assert "http://localhost:3000" not in prod_origins
    assert "http://127.0.0.1:3000" not in prod_origins
    assert prod_origins == ["https://preview.vercel.app"]

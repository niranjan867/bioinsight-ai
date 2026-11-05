import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="API v1 Health Check")
def get_api_health() -> dict[str, str]:
    """Check API v1 status."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "application": settings.APP_NAME,
        "version": "0.1.0",
    }


@router.get("/db", summary="Database Connectivity Health Check")
def get_database_health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Execute a real SQL query to verify database connectivity.

    Never exposes connection strings, internal exception traces, or credentials.
    """
    try:
        db.execute(text("SELECT 1")).scalar_one()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception:
        logger.exception("Database connectivity check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )

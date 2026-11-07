import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.assistant import router as assistant_v1_router
from app.api.v1.auth import router as auth_v1_router
from app.api.v1.compounds import router as compounds_v1_router
from app.api.v1.diseases import router as diseases_v1_router
from app.api.v1.docking import router as docking_v1_router
from app.api.v1.genes import router as genes_v1_router
from app.api.v1.health import router as health_v1_router
from app.api.v1.projects import router as projects_v1_router
from app.api.v1.proteins import router as proteins_v1_router
from app.api.v1.reports import router as reports_v1_router
from app.api.v1.sequences import router as sequences_v1_router
from app.api.v1.structures import router as structures_v1_router
from app.core.config import settings
from app.database.session import get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown procedures."""
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="BioInsight AI — Advanced Multi-Omics & Bioinformatics Research Platform",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS restricted to the configured frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.get("/health", tags=["Health"], summary="Root Health Check")
def root_health() -> dict[str, str]:
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


@app.get("/health/db", tags=["Health"], summary="Root Database Health Check")
def root_database_health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Root endpoint to check database connectivity.

    Executes a real SQL query (SELECT 1). Returns structured JSON.
    Never exposes credentials or internal exception strings.
    """
    try:
        db.execute(text("SELECT 1")).scalar_one()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception:
        logger.exception("Root database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )


# Mount API v1 routers
app.include_router(health_v1_router, prefix="/api/v1")
app.include_router(auth_v1_router, prefix="/api/v1")
app.include_router(projects_v1_router, prefix="/api/v1")
app.include_router(genes_v1_router, prefix="/api/v1")
app.include_router(proteins_v1_router, prefix="/api/v1")
app.include_router(sequences_v1_router, prefix="/api/v1")
app.include_router(diseases_v1_router, prefix="/api/v1")
app.include_router(compounds_v1_router, prefix="/api/v1")
app.include_router(structures_v1_router, prefix="/api/v1")
app.include_router(docking_v1_router, prefix="/api/v1")
app.include_router(assistant_v1_router, prefix="/api/v1")
app.include_router(reports_v1_router, prefix="/api/v1")

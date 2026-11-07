import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_optional_current_user
from app.bioinformatics.databases.registry import registry
from app.bioinformatics.databases.schemas import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    GlobalSearchRequest,
    GlobalSearchResponse,
    NormalizedRecord,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/databases", tags=["Scientific Database Hub"])


@router.get(
    "/connectors",
    response_model=list[ConnectorMetadata],
    summary="List Registered Scientific Database Connectors",
)
def list_connectors() -> list[ConnectorMetadata]:
    """Return catalog of all 11 active scientific database connectors."""
    return registry.list_connectors()


@router.get(
    "/health",
    response_model=list[ConnectorHealthStatus],
    summary="Check Health of All Scientific Database Connectors",
)
async def check_connectors_health() -> list[ConnectorHealthStatus]:
    """Test live connectivity and latency across all external biological APIs."""
    return await registry.check_all_health()


@router.post(
    "/search",
    response_model=GlobalSearchResponse,
    summary="Federated Multi-Database Global Search",
)
async def global_search(
    request: GlobalSearchRequest,
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> GlobalSearchResponse:
    """Execute concurrent search across all configured scientific database connectors.

    Partial failures are captured cleanly: if a single database endpoint times out or errors,
    results from all other databases are preserved without failing the global search request.
    """
    logger.info(
        "Global search query='%s' (user=%s)",
        request.query,
        current_user.email if current_user else "anonymous",
    )
    return await registry.search_all(request)


@router.get(
    "/{database_id}/record/{record_id}",
    response_model=NormalizedRecord,
    summary="Retrieve Normalized Record Detail",
)
async def get_database_record(
    database_id: str,
    record_id: str,
) -> NormalizedRecord:
    """Fetch structured record details by database ID and accession/identifier."""
    connector = registry.get_connector(database_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connector '{database_id}' not found",
        )

    record = await connector.get_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record '{record_id}' not found in database '{database_id}'",
        )
    return record

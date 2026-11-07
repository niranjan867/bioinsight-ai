import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.bioinformatics.diseases.schemas import (
    DiseaseDetailResponse,
    DiseasePublicationsResponse,
    DiseaseSearchResponse,
)
from app.bioinformatics.diseases.service import DiseaseService
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diseases", tags=["Disease Intelligence"])

disease_service = DiseaseService()


@router.get(
    "/search",
    response_model=DiseaseSearchResponse,
    summary="Search diseases across Open Targets Platform",
)
async def search_diseases(
    q: Annotated[str, Query(min_length=2, max_length=150, description="Disease name or phenotype keyword")],
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> DiseaseSearchResponse:
    """Search diseases and clinical phenotypes using the Open Targets Platform API."""
    try:
        return await disease_service.search(query=q.strip(), size=size)
    except Exception as exc:
        logger.exception("Error searching diseases for query: %s", q)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream disease search failed: {exc}",
        ) from exc


@router.get(
    "/{disease_id}",
    response_model=DiseaseDetailResponse,
    summary="Get disease details and associated genetic targets",
)
async def get_disease(
    disease_id: str,
    db: Annotated[Session, Depends(get_db)],
    force_refresh: bool = Query(False, description="Bypass PostgreSQL cache and query upstream"),
) -> DiseaseDetailResponse:
    """Retrieve disease details, therapeutic areas, and target associations."""
    try:
        result = await disease_service.get_disease(
            disease_id=disease_id.strip(),
            db=db,
            force_refresh=force_refresh,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disease with ID '{disease_id}' was not found in Open Targets",
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error retrieving disease '%s'", disease_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream query failed for disease '{disease_id}': {exc}",
        ) from exc


@router.get(
    "/{disease_id}/publications",
    response_model=DiseasePublicationsResponse,
    summary="Search scientific literature for a disease via Europe PMC",
)
async def get_disease_publications(
    disease_id: str,
    name: Annotated[str, Query(min_length=2, description="Disease name to query")],
    size: Annotated[int, Query(ge=1, le=50)] = 15,
) -> DiseasePublicationsResponse:
    """Fetch peer-reviewed publications from Europe PMC for this disease."""
    try:
        return await disease_service.get_publications(
            disease_id=disease_id.strip(),
            disease_name=name.strip(),
            size=size,
        )
    except Exception as exc:
        logger.exception("Error retrieving publications for disease '%s'", disease_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Europe PMC search failed: {exc}",
        ) from exc


import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.bioinformatics.compounds.schemas import (
    Compound3DConformerResponse,
    CompoundDetailResponse,
    CompoundSearchResponse,
    CompoundTargetsResponse,
)
from app.bioinformatics.compounds.service import CompoundService
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compounds", tags=["Compound Intelligence"])

compound_service = CompoundService()


@router.get(
    "/search",
    response_model=CompoundSearchResponse,
    summary="Search chemical compounds across PubChem",
)
async def search_compounds(
    q: Annotated[str, Query(min_length=2, max_length=200, description="Compound name, synonym, or SMILES")],
    limit: Annotated[int, Query(ge=1, le=50)] = 15,
) -> CompoundSearchResponse:
    """Search bioactive compounds by name or chemical formula in PubChem."""
    try:
        return await compound_service.search(query=q.strip(), max_records=limit)
    except Exception as exc:
        logger.exception("Error searching compounds for '%s'", q)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PubChem compound search failed: {exc}",
        ) from exc


@router.get(
    "/{identifier}",
    response_model=CompoundDetailResponse,
    summary="Get compound properties, Lipinski metrics, and drug targets",
)
async def get_compound(
    identifier: str,
    db: Annotated[Session, Depends(get_db)],
    force_refresh: bool = Query(False, description="Bypass cache and query upstream"),
) -> CompoundDetailResponse:
    """Retrieve molecular properties, 2D structure, Lipinski Rule of 5 metrics, and ChEMBL targets."""
    try:
        result = await compound_service.get_compound(
            identifier=identifier.strip(),
            db=db,
            force_refresh=force_refresh,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compound '{identifier}' was not found in PubChem or ChEMBL",
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error retrieving compound '%s'", identifier)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Compound lookup failed for '{identifier}': {exc}",
        ) from exc


@router.get(
    "/{cid}/targets",
    response_model=CompoundTargetsResponse,
    summary="Get biological target proteins from ChEMBL",
)
async def get_compound_targets(
    cid: int,
    db: Annotated[Session, Depends(get_db)],
) -> CompoundTargetsResponse:
    """Fetch mechanism of action and target proteins from ChEMBL for this compound."""
    try:
        return await compound_service.get_targets(cid=cid, db=db)
    except Exception as exc:
        logger.exception("Error retrieving targets for compound CID %d", cid)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch ChEMBL targets: {exc}",
        ) from exc


@router.get(
    "/{cid}/conformer3d",
    response_model=Compound3DConformerResponse,
    summary="Get 3D conformer coordinates in SDF format",
)
async def get_compound_3d_conformer(
    cid: int,
) -> Compound3DConformerResponse:
    """Download 3D spatial conformer coordinates for structural modeling and molecular docking."""
    try:
        conformer = await compound_service.get_3d_conformer(cid=cid)
        if not conformer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"3D conformer not available for compound CID {cid}",
            )
        return conformer
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching 3D conformer for CID %d", cid)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch 3D conformer: {exc}",
        ) from exc


@router.get(
    "/{cid}/sdf",
    summary="Download raw SDF file directly",
)
async def download_compound_sdf(
    cid: int,
) -> Response:
    """Stream raw SDF file for external molecular modeling tools."""
    conformer = await compound_service.get_3d_conformer(cid=cid)
    if not conformer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SDF not available for CID {cid}",
        )
    return Response(
        content=conformer.sdf_data,
        media_type="chemical/x-mdl-sdfile",
        headers={"Content-Disposition": f"attachment; filename=compound_{cid}.sdf"},
    )


import logging

from fastapi import APIRouter, HTTPException, Response, status

from app.bioinformatics.structures.schemas import (
    AlphaFoldMetadataResponse,
    StructureMetadataResponse,
)
from app.bioinformatics.structures.service import StructureService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/structures", tags=["Protein Structure Explorer"])

structure_service = StructureService()


@router.get(
    "/{structure_id}",
    response_model=StructureMetadataResponse,
    summary="Get 3D macromolecular structure metadata from RCSB PDB",
)
async def get_structure_metadata(
    structure_id: str,
) -> StructureMetadataResponse:
    """Retrieve experimental structure metadata, resolution, method, and polymer/ligand entities."""
    try:
        metadata = await structure_service.get_structure_metadata(structure_id=structure_id.strip())
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Structure '{structure_id}' not found in RCSB Protein Data Bank",
            )
        return metadata
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error retrieving structure metadata for %s", structure_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve structure metadata: {exc}",
        ) from exc


@router.get(
    "/{structure_id}/pdb",
    summary="Download or stream raw PDB coordinate file for 3D viewer",
)
async def get_structure_pdb(
    structure_id: str,
) -> Response:
    """Stream raw PDB text format for 3D molecular visualization in 3Dmol.js/Mol*."""
    try:
        pdb_content = await structure_service.get_pdb_file_content(structure_id=structure_id.strip())
        if not pdb_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDB coordinate file not available for structure '{structure_id}'",
            )
        return Response(
            content=pdb_content,
            media_type="chemical/x-pdb",
            headers={"Content-Disposition": f"inline; filename={structure_id.upper()}.pdb"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error downloading PDB coordinate file for %s", structure_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch PDB coordinates: {exc}",
        ) from exc


@router.get(
    "/alphafold/{accession}",
    response_model=AlphaFoldMetadataResponse,
    summary="Get AlphaFold DB predicted structure metadata and confidence",
)
async def get_alphafold_structure(
    accession: str,
) -> AlphaFoldMetadataResponse:
    """Retrieve predicted 3D structure metadata, global pLDDT score, and coordinate links."""
    try:
        af_data = await structure_service.get_alphafold_metadata(accession=accession.strip())
        if not af_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AlphaFold model not available for UniProt accession '{accession}'",
            )
        return af_data
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error querying AlphaFold DB for %s", accession)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch AlphaFold structure: {exc}",
        ) from exc

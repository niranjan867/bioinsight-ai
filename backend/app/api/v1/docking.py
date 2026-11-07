import logging

from fastapi import APIRouter, HTTPException, status

from app.bioinformatics.docking.schemas import (
    DockingAnalysisRequest,
    DockingAnalysisResponse,
    PdbLigandsResponse,
)
from app.bioinformatics.docking.service import DockingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docking", tags=["Protein-Ligand Interaction & Docking"])

docking_service = DockingService()


@router.post(
    "/analyze",
    response_model=DockingAnalysisResponse,
    summary="Perform 3D protein-ligand binding site contact and affinity analysis",
)
async def analyze_docking_interaction(
    payload: DockingAnalysisRequest,
) -> DockingAnalysisResponse:
    """Analyze 3D atomic coordinates between a protein and bound ligand to extract contacts, hydrogen bonds, and binding energy."""
    try:
        result = await docking_service.analyze_interaction(
            pdb_id=payload.pdb_id,
            ligand_id=payload.ligand_id,
            max_distance=payload.max_distance,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No bound ligand found matching '{payload.ligand_id or 'any'}' in PDB structure '{payload.pdb_id}'",
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error analyzing docking interaction for PDB %s", payload.pdb_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Interaction calculation failed: {exc}",
        ) from exc


@router.get(
    "/ligands/{pdb_id}",
    response_model=PdbLigandsResponse,
    summary="Get all bound chemical ligands in a PDB structure",
)
async def get_pdb_ligands(
    pdb_id: str,
) -> PdbLigandsResponse:
    """List all non-water hetero-molecule ligands available in a PDB entry."""
    try:
        return await docking_service.get_pdb_ligands(pdb_id=pdb_id)
    except Exception as exc:
        logger.exception("Error extracting ligands from PDB %s", pdb_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to extract ligands from PDB: {exc}",
        ) from exc

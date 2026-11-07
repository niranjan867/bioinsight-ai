import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.bioinformatics.docking.report import build_docking_report_request
from app.bioinformatics.docking.schemas import (
    BoundingBox,
    DockingAnalysisRequest,
    DockingAnalysisResponse,
    DockingJobDetailResponse,
    DockingJobResponse,
    DockingSubmitRequest,
    LigandPrepRequest,
    LigandPrepResponse,
    PdbLigandsResponse,
    PocketDetectRequest,
    ReceptorPrepRequest,
    ReceptorPrepResponse,
)
from app.bioinformatics.docking.service import DockingService
from app.database.session import get_db
from app.models.user import User
from app.services.reports import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docking", tags=["Molecular Docking Platform"])

docking_service = DockingService()
report_service = ReportService()


@router.post(
    "/prepare/receptor",
    response_model=ReceptorPrepResponse,
    summary="Prepare and validate receptor structure",
)
async def prepare_receptor_endpoint(
    payload: ReceptorPrepRequest,
) -> ReceptorPrepResponse:
    """Download, clean, remove waters, and extract structural geometry from receptor coordinates."""
    try:
        return await docking_service.prepare_receptor_input(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Receptor preparation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Receptor preparation failed: {exc}",
        ) from exc


@router.post(
    "/prepare/ligand",
    response_model=LigandPrepResponse,
    summary="Prepare ligand and generate 3D conformer",
)
async def prepare_ligand_endpoint(
    payload: LigandPrepRequest,
) -> LigandPrepResponse:
    """Validate structure, generate 3D conformer, add hydrogens, and assign partial charges."""
    try:
        return await docking_service.prepare_ligand_input(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Ligand preparation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ligand preparation failed: {exc}",
        ) from exc


@router.post(
    "/pocket",
    response_model=BoundingBox,
    summary="Detect binding pocket bounding box",
)
async def detect_pocket_endpoint(
    payload: PocketDetectRequest,
) -> BoundingBox:
    """Calculate 3D search space bounding box using bound ligand coordinates or residue selections."""
    try:
        return await docking_service.detect_pocket_coordinates(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Pocket detection failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pocket calculation failed: {exc}",
        ) from exc


@router.post(
    "/jobs",
    response_model=DockingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit genuine AutoDock Vina molecular docking job",
)
async def submit_docking_job_endpoint(
    payload: DockingSubmitRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> DockingJobResponse:
    """Submit a molecular docking job for asynchronous execution using AutoDock Vina."""
    try:
        user_id = current_user.id if current_user else None
        return await docking_service.submit_job(db=db, req=payload, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to submit docking job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docking submission failed: {exc}",
        ) from exc


@router.get(
    "/jobs",
    response_model=list[DockingJobResponse],
    summary="List docking jobs",
)
def list_docking_jobs_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[DockingJobResponse]:
    """Retrieve history of docking jobs for the authenticated researcher."""
    user_id = current_user.id if current_user else None
    return docking_service.list_jobs(db=db, user_id=user_id, limit=limit)


@router.get(
    "/jobs/{job_id}",
    response_model=DockingJobDetailResponse,
    summary="Retrieve docking job details, poses, and interaction contacts",
)
def get_docking_job_endpoint(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> DockingJobDetailResponse:
    """Retrieve full results of an AutoDock Vina run including ranked poses and interaction contacts."""
    user_id = current_user.id if current_user else None
    job = docking_service.get_job_detail(db=db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Docking job '{job_id}' not found",
        )
    return job


@router.get(
    "/jobs/{job_id}/report",
    summary="Download publication-ready molecular docking scientific report (PDF or DOCX)",
)
def download_docking_report_endpoint(
    job_id: str,
    format: str = Query(default="pdf", description="Document format ('pdf' or 'docx')"),
    db: Annotated[Session, Depends(get_db)] = ...,
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> Response:
    """Generate and download a comprehensive scientific docking report with ranked poses and contacts."""
    user_id = current_user.id if current_user else None
    job = docking_service.get_job_detail(db=db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Docking job '{job_id}' not found",
        )

    author_name = current_user.username if current_user else "BioInsight AI Researcher"
    report_req = build_docking_report_request(job=job, author_name=author_name)

    fmt = format.lower().strip()
    clean_target = (job.protein_name or "target").lower().replace(" ", "_")[:15]
    clean_ligand = (job.ligand_name or "ligand").lower().replace(" ", "_")[:15]
    filename = f"docking_{clean_target}_{clean_ligand}_{job.id[:6]}.{fmt}"

    if fmt == "docx":
        docx_bytes = report_service.generate_docx(report_req)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif fmt == "pdf":
        pdf_bytes = report_service.generate_pdf(report_req)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Only 'pdf' and 'docx' are supported.",
        )


# -------------------------------------------------------------
# Backward-Compatible Legacy Endpoints
# -------------------------------------------------------------


@router.post(
    "/analyze",
    response_model=DockingAnalysisResponse,
    summary="Perform 3D protein-ligand binding site contact and affinity analysis",
)
async def analyze_docking_interaction(
    payload: DockingAnalysisRequest,
) -> DockingAnalysisResponse:
    """Analyze 3D atomic coordinates between a protein and bound ligand."""
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
    return await docking_service.get_pdb_ligands(pdb_id=pdb_id)

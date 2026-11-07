import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.reports import GenerateReportRequest, ReportSection
from app.services.reports import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Research Report Generator"])

report_service = ReportService()


@router.post(
    "/pdf",
    summary="Generate and download a publication-grade PDF report",
)
def generate_pdf_report(
    payload: GenerateReportRequest,
) -> Response:
    """Generate a PDF research report with summary, tables, and references."""
    try:
        pdf_bytes = report_service.generate_pdf(payload)
        filename = f"{payload.title.lower().replace(' ', '_')[:30]}_report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        logger.exception("PDF generation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {exc}",
        ) from exc


@router.post(
    "/docx",
    summary="Generate and download an editable DOCX research document",
)
def generate_docx_report(
    payload: GenerateReportRequest,
) -> Response:
    """Generate a Microsoft Word DOCX research report."""
    try:
        docx_bytes = report_service.generate_docx(payload)
        filename = f"{payload.title.lower().replace(' ', '_')[:30]}_report.docx"
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        logger.exception("DOCX generation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {exc}",
        ) from exc


@router.get(
    "/project/{project_id}/pdf",
    summary="Export full project report as PDF",
)
def export_project_pdf(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Export all research findings, saved targets, and audit log for a project as PDF."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # Format items table
    item_rows = [["Type", "Identifier", "Title", "Date Added"]]
    for item in project.items:
        item_rows.append([
            item.item_type.upper(),
            item.item_id,
            item.title[:40],
            item.created_at.strftime("%Y-%m-%d"),
        ])

    # Format activity table
    act_rows = [["Action", "Timestamp", "Details"]]
    for act in project.activities[:15]:
        details_str = str(act.details) if act.details else "Completed"
        act_rows.append([
            act.action.replace("_", " ").title(),
            act.created_at.strftime("%Y-%m-%d %H:%M"),
            details_str[:50],
        ])

    sections = [
        ReportSection(
            title="Project Metadata & Configuration",
            content=(
                f"Status: {project.status.upper()} | Tags: {', '.join(project.tags or ['None'])}\n"
                f"Description: {project.description or 'No description provided.'}\n"
                f"Total Saved Scientific Targets: {len(project.items)}"
            ),
        ),
        ReportSection(
            title="Curated Scientific Items & Targets",
            content="Summary of genomic, proteomic, and pharmacological entities associated with this investigation.",
            table_data=item_rows if len(project.items) > 0 else None,
        ),
        ReportSection(
            title="Audit Trail & Investigation History",
            content="Timeline of laboratory calculations, alignments, and targets added to this workspace.",
            table_data=act_rows if len(project.activities) > 0 else None,
        ),
    ]

    report_req = GenerateReportRequest(
        title=f"Project Report: {project.name}",
        subtitle=f"BioInsight AI Multi-Omics Research Dossier (Project ID: {project.id})",
        author_name=current_user.full_name,
        summary=(
            f"This dossier compiles curated multi-omics data, molecular targets, and experimental audit trails for '{project.name}'. "
            f"All entries are cross-referenced with official biological repositories (NCBI, UniProt, Open Targets, PubChem) and local computational assays."
        ),
        sections=sections,
        references=[
            "MyGene.info / NCBI Entrez Gene",
            "UniProt Knowledgebase (UniProtKB)",
            "Open Targets Platform API v4",
            "PubChem PUG REST API",
            "Biopython 1.88 Laboratory Suite",
        ],
    )

    pdf_bytes = report_service.generate_pdf(report_req)
    filename = f"project_{project.id}_{project.name.lower().replace(' ', '_')[:20]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/project/{project_id}/docx",
    summary="Export full project report as DOCX",
)
def export_project_docx(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Export project dossier as an editable Word document."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    item_rows = [["Type", "Identifier", "Title", "Date Added"]]
    for item in project.items:
        item_rows.append([
            item.item_type.upper(),
            item.item_id,
            item.title[:40],
            item.created_at.strftime("%Y-%m-%d"),
        ])

    sections = [
        ReportSection(
            title="Project Metadata & Configuration",
            content=f"Status: {project.status.upper()} | Tags: {', '.join(project.tags or ['None'])}\nDescription: {project.description or 'N/A'}",
        ),
        ReportSection(
            title="Curated Scientific Items & Targets",
            content="Summary of genomic, proteomic, and pharmacological entities associated with this investigation.",
            table_data=item_rows if len(project.items) > 0 else None,
        ),
    ]

    report_req = GenerateReportRequest(
        title=f"Project Report: {project.name}",
        subtitle=f"BioInsight AI Multi-Omics Research Dossier (Project ID: {project.id})",
        author_name=current_user.full_name,
        summary=f"Curated findings for {project.name}.",
        sections=sections,
        references=["NCBI Entrez", "UniProtKB", "Open Targets", "PubChem"],
    )

    docx_bytes = report_service.generate_docx(report_req)
    filename = f"project_{project.id}_{project.name.lower().replace(' ', '_')[:20]}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.bioinformatics.assistant.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
)
from app.bioinformatics.assistant.service import AssistantService
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["AI Research Assistant"])

assistant_service = AssistantService()


@router.post(
    "/chat",
    response_model=AssistantQueryResponse,
    summary="Query the scientific research assistant with grounded citations",
)
async def query_research_assistant(
    payload: AssistantQueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AssistantQueryResponse:
    """Answer scientific research questions grounded in real-time data from biological databases."""
    try:
        return await assistant_service.answer_query(payload=payload, db=db)
    except Exception as exc:
        logger.exception("Error processing assistant query: %s", payload.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant engine error: {exc}",
        ) from exc


@router.get(
    "/suggestions",
    response_model=list[str],
    summary="Get recommended research prompts",
)
def get_query_suggestions() -> list[str]:
    """Return common scientific query prompts across genomics, proteomics, and pharmacology."""
    return [
        "What are the genomic coordinates and functional summary for human BRCA1?",
        "Compare molecular properties and Lipinski compliance of Aspirin vs Metformin",
        "What is the sequence length, mass, and subcellular location of human Hemoglobin Beta (P68871)?",
        "What are the top genetic targets associated with Asthma in Open Targets?",
        "Explain the function of TP53 and list its key biological roles",
    ]


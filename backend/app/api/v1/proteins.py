import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.bioinformatics.proteins.client import ProteinClientError, ProteinNotFoundError
from app.bioinformatics.proteins.schemas import (
    ProteinDetailResponse,
    ProteinReferencesResponse,
    ProteinSearchResponse,
    ProteinSequenceAnalysisResponse,
    ProteinStructuresResponse,
)
from app.bioinformatics.proteins.service import protein_service
from app.bioinformatics.proteins.utils import is_valid_uniprot_accession
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proteins", tags=["Protein Intelligence"])


@router.get(
    "/search",
    response_model=ProteinSearchResponse,
    summary="Search proteins in UniProtKB",
    description="Search protein entries by protein name, gene symbol, keyword, or accession in UniProtKB.",
)
async def search_proteins(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            description="Protein name, gene symbol, UniProt accession, or keyword (e.g. hemoglobin, TP53, kinase)",
        ),
    ],
    species: Annotated[
        str,
        Query(
            max_length=50,
            description="Organism filter (e.g. human, mouse, rat, zebrafish, fruitfly, yeast, nematode, all)",
        ),
    ] = "human",
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Maximum number of biological hits to return (1-50)",
        ),
    ] = 15,
) -> ProteinSearchResponse:
    """Execute protein search across UniProtKB with organism filtering."""
    try:
        return await protein_service.search(query=q, species=species, limit=limit)
    except ProteinClientError as exc:
        logger.warning("Protein search failed for query '%s': %s", q, exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during protein search for query '%s'", q)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Biological protein database query failed. Please verify network access or try again shortly.",
        ) from exc


@router.get(
    "/{accession}",
    response_model=ProteinDetailResponse,
    summary="Get detailed biological protein record",
    description="Retrieve comprehensive protein record from UniProtKB with sequence, function, cellular localization, and PostgreSQL caching.",
)
async def get_protein_detail(
    accession: Annotated[
        str,
        Path(
            min_length=3,
            max_length=32,
            description="UniProt accession (e.g. P68871, P04637, Q9BYF1)",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    force_refresh: Annotated[
        bool,
        Query(
            description="Bypass PostgreSQL cache and retrieve fresh record from UniProtKB",
        ),
    ] = False,
) -> ProteinDetailResponse:
    """Retrieve full protein record with automatic PostgreSQL caching and cross-reference enrichment."""
    if not is_valid_uniprot_accession(accession):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UniProt accession format '{accession}'. Expected standard accession (e.g. P68871, P04637).",
        )

    try:
        return await protein_service.get_protein(
            accession=accession,
            db=db,
            force_refresh=force_refresh,
        )
    except ProteinNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein '{accession}' not found in biological databases.",
        ) from exc
    except ProteinClientError as exc:
        logger.warning("Protein client error for '%s': %s", accession, exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving protein record for '%s'", accession)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve protein record from biological database.",
        ) from exc


@router.get(
    "/{accession}/sequence",
    response_model=ProteinSequenceAnalysisResponse,
    summary="Get protein sequence and computational physicochemical analysis",
    description="Retrieve primary amino acid sequence with FASTA export and genuine Biopython sequence analysis (MW, pI, instability, GRAVY, aromaticity).",
)
async def get_protein_sequence(
    accession: Annotated[
        str,
        Path(
            min_length=3,
            max_length=32,
            description="UniProt accession",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ProteinSequenceAnalysisResponse:
    """Execute Biopython computational sequence analysis on verified protein sequence."""
    if not is_valid_uniprot_accession(accession):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UniProt accession format '{accession}'.",
        )

    try:
        return await protein_service.get_sequence(accession=accession, db=db)
    except ProteinNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein '{accession}' not found.",
        ) from exc
    except ProteinClientError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error analyzing sequence for '%s'", accession)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to execute protein sequence analysis.",
        ) from exc


@router.get(
    "/{accession}/structures",
    response_model=ProteinStructuresResponse,
    summary="Get 3D macromolecular structures (PDB and AlphaFold)",
    description="Retrieve experimentally determined structures from RCSB PDB and predicted 3D models from AlphaFold DB, clearly separated by provenance.",
)
async def get_protein_structures(
    accession: Annotated[
        str,
        Path(
            min_length=3,
            max_length=32,
            description="UniProt accession",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ProteinStructuresResponse:
    """Retrieve 3D atomic structures and AlphaFold predictions for an inspected protein."""
    if not is_valid_uniprot_accession(accession):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UniProt accession format '{accession}'.",
        )

    try:
        return await protein_service.get_structures(accession=accession, db=db)
    except ProteinNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein '{accession}' not found.",
        ) from exc
    except ProteinClientError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving structures for '%s'", accession)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve macromolecular structures.",
        ) from exc


@router.get(
    "/{accession}/references",
    response_model=ProteinReferencesResponse,
    summary="Get verified cross-database references",
    description="Retrieve outbound direct links to UniProtKB, RCSB PDB, AlphaFold DB, GeneCards, and Ensembl.",
)
async def get_protein_references(
    accession: Annotated[
        str,
        Path(
            min_length=3,
            max_length=32,
            description="UniProt accession",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ProteinReferencesResponse:
    """Fetch external database links for an inspected protein."""
    if not is_valid_uniprot_accession(accession):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UniProt accession format '{accession}'.",
        )

    try:
        return await protein_service.get_references(accession=accession, db=db)
    except ProteinNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein '{accession}' not found.",
        ) from exc
    except ProteinClientError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving references for '%s'", accession)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve cross-references.",
        ) from exc


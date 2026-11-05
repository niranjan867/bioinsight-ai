import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.bioinformatics.genes.client import GeneClientError, GeneNotFoundError
from app.bioinformatics.genes.schemas import (
    GeneDetailResponse,
    GeneReferencesResponse,
    GeneSearchResponse,
)
from app.bioinformatics.genes.service import gene_service
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/genes", tags=["Gene Intelligence"])


@router.get(
    "/search",
    response_model=GeneSearchResponse,
    summary="Search genes in biological databases",
    description="Search genes by symbol, name, accession, or keyword using MyGene.info and NCBI Entrez APIs.",
)
async def search_genes(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            description="Gene symbol, Entrez ID, Ensembl ID, or keyword (e.g. BRCA1, TP53, kinase)",
        ),
    ],
    species: Annotated[
        str,
        Query(
            max_length=50,
            description="Organism filter (e.g. human, mouse, rat, zebrafish, fruitfly, c_elegans, yeast, all)",
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
) -> GeneSearchResponse:
    """Search genes across official biological repositories with organism filtering."""
    try:
        return await gene_service.search(query=q, species=species, limit=limit)
    except GeneClientError as exc:
        logger.warning("Gene search failed for query '%s': %s", q, exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during gene search for query '%s'", q)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Biological database query failed. Please verify network access or try again shortly.",
        ) from exc


@router.get(
    "/{gene_id}",
    response_model=GeneDetailResponse,
    summary="Get detailed biological gene record",
    description="Retrieve comprehensive gene annotation, genomic coordinates, aliases, summary, and external database links.",
)
async def get_gene_detail(
    gene_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=100,
            description="Official gene symbol (e.g. BRCA1), Entrez ID (e.g. 672), or Ensembl ID",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    force_refresh: Annotated[
        bool,
        Query(
            description="Bypass PostgreSQL cache and retrieve fresh data from upstream biological databases",
        ),
    ] = False,
) -> GeneDetailResponse:
    """Retrieve full gene record with automatic PostgreSQL caching and cross-reference generation."""
    try:
        return await gene_service.get_gene(
            gene_id=gene_id,
            db=db,
            force_refresh=force_refresh,
        )
    except GeneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene '{gene_id}' not found in biological databases.",
        ) from exc
    except GeneClientError as exc:
        logger.warning("Gene client error for '%s': %s", gene_id, exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving gene record for '%s'", gene_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve gene record from biological databases.",
        ) from exc


@router.get(
    "/{gene_id}/references",
    response_model=GeneReferencesResponse,
    summary="Get verified database cross-references",
    description="Retrieve direct cross-reference URLs to NCBI Gene, Ensembl, HGNC, GeneCards, and OMIM.",
)
async def get_gene_references(
    gene_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=100,
            description="Official gene symbol or Entrez identifier",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> GeneReferencesResponse:
    """Fetch external database links for an inspected gene."""
    try:
        return await gene_service.get_references(gene_id=gene_id, db=db)
    except GeneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene '{gene_id}' not found.",
        ) from exc
    except GeneClientError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving references for '%s'", gene_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve cross-references.",
        ) from exc

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.bioinformatics.genes.client import (
    GeneApiClient,
    GeneNotFoundError,
    gene_client,
)
from app.bioinformatics.genes.schemas import (
    GeneDetailResponse,
    GeneReferencesResponse,
    GeneSearchResponse,
    GeneSearchResult,
    GenomicLocation,
)
from app.bioinformatics.genes.utils import (
    build_external_references,
    normalize_gene_query,
    normalize_species,
)
from app.models.gene_cache import GeneCache

logger = logging.getLogger(__name__)

CACHE_TTL_DAYS = 7


def _extract_genomic_location(raw_pos: Any) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """Parse genomic position dictionary or list from biological API payload."""
    pos_data = raw_pos
    if isinstance(raw_pos, list) and len(raw_pos) > 0:
        pos_data = raw_pos[0]

    if isinstance(pos_data, dict):
        chrom = str(pos_data.get("chr") or "") or None
        start = pos_data.get("start")
        end = pos_data.get("end")
        strand = pos_data.get("strand")
        ensembl_gene = pos_data.get("ensemblgene")
        return chrom, start, end, strand, ensembl_gene

    return None, None, None, None, None


def _extract_ensembl_id(ensembl_data: Any) -> str | None:
    """Extract primary Ensembl gene identifier from diverse payload shapes."""
    if isinstance(ensembl_data, dict):
        gene_val = ensembl_data.get("gene")
        if isinstance(gene_val, str):
            return gene_val
        if isinstance(gene_val, list) and len(gene_val) > 0:
            return str(gene_val[0])
    elif isinstance(ensembl_data, list) and len(ensembl_data) > 0:
        first = ensembl_data[0]
        if isinstance(first, dict):
            return first.get("gene")
        if isinstance(first, str):
            return first
    return None


class GeneService:
    """Core bioinformatics business service for gene search, retrieval, and persistent caching."""

    def __init__(self, client: GeneApiClient = gene_client):
        self.client = client

    async def search(
        self,
        query: str,
        species: str = "human",
        limit: int = 15,
    ) -> GeneSearchResponse:
        """Search genes across biological databases by symbol, accession, or keyword."""
        clean_query = normalize_gene_query(query)
        clean_species = normalize_species(species)

        payload = await self.client.search_mygene(
            query=clean_query,
            species=clean_species,
            limit=limit,
        )

        hits = payload.get("hits", [])
        total = payload.get("total", len(hits))
        results: list[GeneSearchResult] = []

        for hit in hits:
            gene_id = str(hit.get("_id") or hit.get("entrezgene") or "")
            symbol = str(hit.get("symbol") or hit.get("_id") or "")
            if not gene_id or not symbol:
                continue

            # Extract Ensembl ID
            ensembl_id = _extract_ensembl_id(hit.get("ensembl"))

            # Extract chromosome
            chrom, _, _, _, _ = _extract_genomic_location(hit.get("genomic_pos"))

            # Extract aliases
            raw_aliases = hit.get("alias", [])
            aliases = [raw_aliases] if isinstance(raw_aliases, str) else list(raw_aliases or [])

            results.append(
                GeneSearchResult(
                    id=gene_id,
                    symbol=symbol,
                    name=hit.get("name"),
                    species=clean_species,
                    taxid=hit.get("taxid"),
                    entrez_id=str(hit.get("entrezgene")) if hit.get("entrezgene") else None,
                    ensembl_id=ensembl_id,
                    chromosome=chrom,
                    type_of_gene=hit.get("type_of_gene"),
                    aliases=aliases,
                    score=hit.get("_score"),
                )
            )

        return GeneSearchResponse(
            query=clean_query,
            species=clean_species,
            total=total,
            results=results,
            source="MyGene.info / NCBI Entrez Gene",
        )

    async def get_gene(
        self,
        gene_id: str,
        db: Session,
        force_refresh: bool = False,
    ) -> GeneDetailResponse:
        """Retrieve comprehensive gene record, utilizing PostgreSQL cache when fresh."""
        clean_id = gene_id.strip()
        if not clean_id:
            raise GeneNotFoundError(clean_id)

        now = datetime.now(UTC)
        freshness_cutoff = now - timedelta(days=CACHE_TTL_DAYS)

        # 1. Check PostgreSQL cache
        if not force_refresh:
            stmt = select(GeneCache).where(
                or_(
                    GeneCache.gene_id == clean_id,
                    GeneCache.symbol.ilike(clean_id),
                    GeneCache.entrez_id == clean_id,
                    GeneCache.ensembl_id == clean_id,
                )
            )
            cached_record = db.execute(stmt).scalars().first()

            if cached_record:
                rec_updated_at = cached_record.updated_at
                if rec_updated_at.tzinfo is None:
                    rec_updated_at = rec_updated_at.replace(tzinfo=UTC)

                if rec_updated_at >= freshness_cutoff:
                    aliases_list: list[str] = []
                if cached_record.aliases:
                    try:
                        aliases_list = json.loads(cached_record.aliases)
                    except (json.JSONDecodeError, TypeError, ValueError):
                        aliases_list = [a.strip() for a in cached_record.aliases.split(",") if a.strip()]

                refs = build_external_references(
                    symbol=cached_record.symbol,
                    entrez_id=cached_record.entrez_id,
                    ensembl_id=cached_record.ensembl_id,
                    species=cached_record.species,
                    taxid=cached_record.taxid,
                )

                genomic_loc = None
                if cached_record.chromosome or cached_record.genomic_start or cached_record.genomic_end:
                    genomic_loc = GenomicLocation(
                        chromosome=cached_record.chromosome,
                        start=cached_record.genomic_start,
                        end=cached_record.genomic_end,
                        strand=cached_record.strand,
                        ensembl_gene_id=cached_record.ensembl_id,
                    )

                return GeneDetailResponse(
                    id=cached_record.gene_id,
                    symbol=cached_record.symbol,
                    name=cached_record.name,
                    species=cached_record.species,
                    taxid=cached_record.taxid,
                    entrez_id=cached_record.entrez_id,
                    ensembl_id=cached_record.ensembl_id,
                    type_of_gene=cached_record.type_of_gene,
                    chromosome=cached_record.chromosome,
                    genomic_location=genomic_loc,
                    aliases=aliases_list,
                    summary=cached_record.summary,
                    references=refs,
                    source=f"PostgreSQL Cache ({cached_record.source})",
                    retrieved_at=cached_record.updated_at.isoformat(),
                    cached=True,
                )

        # 2. Fetch fresh record from MyGene.info API
        record = await self.client.get_mygene_record(clean_id)

        canonical_id = str(record.get("_id") or record.get("entrezgene") or clean_id)
        symbol = str(record.get("symbol") or clean_id)
        name = record.get("name")
        taxid = record.get("taxid")
        entrez_id = str(record.get("entrezgene")) if record.get("entrezgene") else None
        ensembl_id = _extract_ensembl_id(record.get("ensembl"))
        type_of_gene = record.get("type_of_gene")

        chrom, start, end, strand, ens_gene = _extract_genomic_location(record.get("genomic_pos"))
        if not ensembl_id and ens_gene:
            ensembl_id = ens_gene

        summary = record.get("summary")
        # If summary is missing or brief, attempt NCBI summary enrichment
        if not summary and entrez_id:
            ncbi_data = await self.client.get_ncbi_summary(entrez_id)
            if ncbi_data:
                summary = ncbi_data.get("summary") or ncbi_data.get("description")
                if not chrom and ncbi_data.get("chromosome"):
                    chrom = str(ncbi_data.get("chromosome"))

        raw_aliases = record.get("alias", [])
        aliases_list = [raw_aliases] if isinstance(raw_aliases, str) else list(raw_aliases or [])

        species = "human" if taxid == 9606 else str(record.get("taxid") or "all")

        refs = build_external_references(
            symbol=symbol,
            entrez_id=entrez_id,
            ensembl_id=ensembl_id,
            species=species,
            taxid=taxid,
        )

        genomic_loc = None
        if chrom or start or end:
            genomic_loc = GenomicLocation(
                chromosome=chrom,
                start=start,
                end=end,
                strand=strand,
                ensembl_gene_id=ensembl_id,
            )

        # 3. Upsert into PostgreSQL cache
        try:
            stmt = select(GeneCache).where(GeneCache.gene_id == canonical_id)
            existing = db.execute(stmt).scalars().first()

            if existing:
                existing.symbol = symbol
                existing.name = name
                existing.species = species
                existing.taxid = taxid
                existing.entrez_id = entrez_id
                existing.ensembl_id = ensembl_id
                existing.chromosome = chrom
                existing.genomic_start = start
                existing.genomic_end = end
                existing.strand = strand
                existing.type_of_gene = type_of_gene
                existing.summary = summary
                existing.aliases = json.dumps(aliases_list)
                existing.source = "MyGene.info / NCBI Entrez"
                existing.source_data = record
                existing.updated_at = now
            else:
                new_entry = GeneCache(
                    gene_id=canonical_id,
                    symbol=symbol,
                    name=name,
                    species=species,
                    taxid=taxid,
                    entrez_id=entrez_id,
                    ensembl_id=ensembl_id,
                    chromosome=chrom,
                    genomic_start=start,
                    genomic_end=end,
                    strand=strand,
                    type_of_gene=type_of_gene,
                    summary=summary,
                    aliases=json.dumps(aliases_list),
                    source="MyGene.info / NCBI Entrez",
                    source_data=record,
                    retrieved_at=now,
                    updated_at=now,
                )
                db.add(new_entry)

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning("Failed to commit gene cache record to PostgreSQL: %s", exc)

        return GeneDetailResponse(
            id=canonical_id,
            symbol=symbol,
            name=name,
            species=species,
            taxid=taxid,
            entrez_id=entrez_id,
            ensembl_id=ensembl_id,
            type_of_gene=type_of_gene,
            chromosome=chrom,
            genomic_location=genomic_loc,
            aliases=aliases_list,
            summary=summary,
            references=refs,
            source="MyGene.info / NCBI Entrez Gene",
            retrieved_at=now.isoformat(),
            cached=False,
        )

    async def get_references(
        self,
        gene_id: str,
        db: Session,
    ) -> GeneReferencesResponse:
        """Fetch verified cross-database references for a gene."""
        gene = await self.get_gene(gene_id=gene_id, db=db)
        return GeneReferencesResponse(
            gene_id=gene.id,
            symbol=gene.symbol,
            references=gene.references,
            source="NCBI Entrez / Ensembl / HGNC / OMIM / GeneCards",
        )


# Default shared service instance
gene_service = GeneService()

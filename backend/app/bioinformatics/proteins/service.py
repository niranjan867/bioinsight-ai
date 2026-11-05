import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.bioinformatics.proteins.client import (
    ProteinApiClient,
    protein_client,
)
from app.bioinformatics.proteins.schemas import (
    AlphaFoldStructure,
    PdbStructure,
    ProteinDetailResponse,
    ProteinReferencesResponse,
    ProteinSearchResponse,
    ProteinSearchResult,
    ProteinSequenceAnalysisResponse,
    ProteinStructuresResponse,
)
from app.bioinformatics.proteins.utils import (
    analyze_protein_sequence,
    build_protein_references,
    normalize_species_for_uniprot,
    validate_uniprot_accession,
)
from app.models.protein_cache import ProteinCache

logger = logging.getLogger(__name__)

CACHE_TTL_DAYS = 7


def _extract_protein_name(data: dict[str, Any]) -> str:
    """Extract approved or recommended protein name from UniProt entry."""
    desc = data.get("proteinDescription", {})
    rec = desc.get("recommendedName", {})
    if rec and "fullName" in rec:
        val = rec["fullName"].get("value")
        if val:
            return str(val)

    sub = desc.get("submissionNames", [])
    if isinstance(sub, list) and len(sub) > 0:
        val = sub[0].get("fullName", {}).get("value")
        if val:
            return str(val)

    alt = desc.get("alternativeNames", [])
    if isinstance(alt, list) and len(alt) > 0:
        val = alt[0].get("fullName", {}).get("value")
        if val:
            return str(val)

    return str(data.get("primaryAccession") or "Unnamed Protein")


def _extract_gene_name(data: dict[str, Any]) -> str | None:
    """Extract primary gene symbol from UniProt entry."""
    genes = data.get("genes", [])
    if isinstance(genes, list) and len(genes) > 0:
        first = genes[0]
        if isinstance(first, dict):
            gn = first.get("geneName")
            if isinstance(gn, dict):
                return gn.get("value")
    return None


def _extract_comment_text(comments: list[dict[str, Any]], comment_type: str) -> str | None:
    """Extract narrative text for specified comment category (e.g. FUNCTION, SUBCELLULAR LOCATION)."""
    texts: list[str] = []
    for c in comments:
        if c.get("commentType") == comment_type:
            if comment_type == "SUBCELLULAR LOCATION":
                sub_locs = c.get("subcellularLocations", [])
                for sl in sub_locs:
                    loc = sl.get("location", {}).get("value")
                    if loc:
                        texts.append(str(loc))
            else:
                for t in c.get("texts", []):
                    val = t.get("value")
                    if val:
                        texts.append(str(val))
    return " ".join(texts) if texts else None


def _extract_ptms(comments: list[dict[str, Any]], features: list[dict[str, Any]]) -> list[str]:
    """Extract post-translational modification descriptions."""
    ptms: list[str] = []
    for c in comments:
        if c.get("commentType") == "PTM":
            for t in c.get("texts", []):
                val = t.get("value")
                if val and val not in ptms:
                    ptms.append(str(val))

    for f in features:
        if f.get("type") in ("Modified residue", "Glycosylation", "Lipidation", "Disulfide bond"):
            desc = f.get("description")
            loc = f.get("location", {})
            start = loc.get("start", {}).get("value")
            f_type = f.get("type")
            entry = f"{f_type}: {desc or 'Modification'} at position {start}" if start else f"{f_type}: {desc}"
            if entry not in ptms:
                ptms.append(entry)

    return ptms[:15]  # Top 15 PTM entries


def _extract_features_summary(features: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate counts of biological sequence features."""
    summary: dict[str, int] = {}
    for f in features:
        f_type = str(f.get("type") or "Other")
        summary[f_type] = summary.get(f_type, 0) + 1
    return summary


def _parse_pdb_crossrefs(cross_refs: list[dict[str, Any]]) -> list[PdbStructure]:
    """Construct PdbStructure models from UniProt PDB cross-references."""
    pdbs: list[PdbStructure] = []
    for cr in cross_refs:
        if cr.get("database") == "PDB":
            pdb_id = cr.get("id")
            if not pdb_id:
                continue
            props = {p.get("key"): p.get("value") for p in cr.get("properties", [])}
            method = props.get("Method", "X-ray diffraction")
            res_str = props.get("Resolution", "")
            res_val: float | None = None
            if res_str:
                res_clean = res_str.replace("A", "").strip()
                try:
                    res_val = float(res_clean)
                except ValueError:
                    res_val = None
            chains = props.get("Chains")

            pdbs.append(
                PdbStructure(
                    pdb_id=pdb_id,
                    title=f"Experimental 3D structure ({pdb_id})",
                    method=method,
                    resolution_angstrom=res_val,
                    chains=chains,
                    deposition_date=None,
                    url=f"https://www.rcsb.org/structure/{pdb_id}",
                    is_experimental=True,
                )
            )
    return pdbs


def _get_plddt_category(plddt: float | None) -> str | None:
    """Classify AlphaFold pLDDT prediction confidence."""
    if plddt is None:
        return None
    if plddt >= 90.0:
        return "Very High (>90 pLDDT)"
    if plddt >= 70.0:
        return "Confident (70-90 pLDDT)"
    if plddt >= 50.0:
        return "Low (50-70 pLDDT)"
    return "Very Low (<50 pLDDT)"


class ProteinService:
    """Core bioinformatics business service for protein search, retrieval, structural analysis, and caching."""

    def __init__(self, client: ProteinApiClient = protein_client):
        self.client = client

    async def search(
        self,
        query: str,
        species: str = "human",
        limit: int = 15,
    ) -> ProteinSearchResponse:
        """Search protein entries across UniProtKB with organism filtering."""
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Protein search query cannot be empty")

        taxid = normalize_species_for_uniprot(species)
        payload = await self.client.search_uniprot(
            query=clean_query,
            taxid=taxid,
            limit=limit,
        )

        raw_results = payload.get("results", [])
        total = payload.get("total", len(raw_results))
        results: list[ProteinSearchResult] = []

        for item in raw_results:
            acc = str(item.get("primaryAccession") or "")
            if not acc:
                continue

            entry_name = item.get("uniProtkbId")
            protein_name = _extract_protein_name(item)
            gene_name = _extract_gene_name(item)
            organism = item.get("organism", {}).get("scientificName", "Unknown")
            item_taxid = item.get("organism", {}).get("taxonId")
            seq_len = item.get("sequence", {}).get("length", 0)
            reviewed = "Swiss-Prot" in str(item.get("entryType") or "")
            score = item.get("score")

            results.append(
                ProteinSearchResult(
                    accession=acc,
                    entry_name=entry_name,
                    protein_name=protein_name,
                    gene_name=gene_name,
                    organism=organism,
                    taxid=item_taxid,
                    length=seq_len,
                    reviewed=reviewed,
                    score=score,
                )
            )

        return ProteinSearchResponse(
            query=clean_query,
            species=species,
            total=total,
            results=results,
            source="UniProtKB (Swiss-Prot / TrEMBL)",
        )

    async def get_protein(
        self,
        accession: str,
        db: Session,
        force_refresh: bool = False,
    ) -> ProteinDetailResponse:
        """Retrieve comprehensive biological protein record, utilizing PostgreSQL cache when fresh."""
        clean_acc = validate_uniprot_accession(accession)
        now = datetime.now(UTC)
        freshness_cutoff = now - timedelta(days=CACHE_TTL_DAYS)

        # 1. Check PostgreSQL cache
        if not force_refresh:
            stmt = select(ProteinCache).where(ProteinCache.accession == clean_acc)
            cached_record = db.execute(stmt).scalars().first()

            if cached_record:
                rec_updated_at = cached_record.updated_at
                if rec_updated_at.tzinfo is None:
                    rec_updated_at = rec_updated_at.replace(tzinfo=UTC)

                if rec_updated_at >= freshness_cutoff:
                    raw_data = cached_record.source_data or {}
                    comments = raw_data.get("comments", [])
                    features = raw_data.get("features", [])
                    cross_refs = raw_data.get("uniProtKBCrossReferences", [])

                    ptms = _extract_ptms(comments, features)
                    feat_summary = _extract_features_summary(features)
                    pdb_refs = _parse_pdb_crossrefs(cross_refs)

                    # Check for AlphaFold
                    has_alphafold = any(cr.get("database") == "AlphaFoldDB" for cr in cross_refs)
                    pdb_ids = [p.pdb_id for p in pdb_refs]

                    refs = build_protein_references(
                        accession=cached_record.accession,
                        gene_name=cached_record.gene_name,
                        organism=cached_record.organism,
                        pdb_ids=pdb_ids,
                        cross_refs=cross_refs,
                    )

                    return ProteinDetailResponse(
                        accession=cached_record.accession,
                        entry_name=cached_record.entry_name,
                        protein_name=cached_record.protein_name,
                        gene_name=cached_record.gene_name,
                        organism=cached_record.organism,
                        taxid=cached_record.taxid,
                        sequence_length=cached_record.length,
                        sequence=cached_record.sequence,
                        mass_da=cached_record.mass,
                        function_summary=cached_record.function_summary,
                        subcellular_location=cached_record.subcellular_location,
                        protein_existence=raw_data.get("proteinExistence"),
                        ptms=ptms,
                        features_summary=feat_summary,
                        pdb_structures_count=len(pdb_refs),
                        has_alphafold=has_alphafold,
                        references=refs,
                        source=f"PostgreSQL Cache ({cached_record.source})",
                        retrieved_at=cached_record.updated_at.isoformat(),
                        cached=True,
                    )

        # 2. Fetch fresh record from UniProtKB
        record = await self.client.get_uniprot_entry(clean_acc)

        canonical_acc = str(record.get("primaryAccession") or clean_acc)
        entry_name = record.get("uniProtkbId")
        protein_name = _extract_protein_name(record)
        gene_name = _extract_gene_name(record)
        organism = record.get("organism", {}).get("scientificName", "Unknown")
        taxid = record.get("organism", {}).get("taxonId")
        seq_data = record.get("sequence", {})
        sequence = str(seq_data.get("value") or "")
        seq_length = seq_data.get("length", len(sequence))
        mass_da = seq_data.get("molWeight")

        comments = record.get("comments", [])
        features = record.get("features", [])
        cross_refs = record.get("uniProtKBCrossReferences", [])

        function_summary = _extract_comment_text(comments, "FUNCTION")
        subcellular_loc = _extract_comment_text(comments, "SUBCELLULAR LOCATION")
        protein_existence = record.get("proteinExistence")

        ptms = _extract_ptms(comments, features)
        feat_summary = _extract_features_summary(features)
        pdb_refs = _parse_pdb_crossrefs(cross_refs)
        has_alphafold = any(cr.get("database") == "AlphaFoldDB" for cr in cross_refs)
        pdb_ids = [p.pdb_id for p in pdb_refs]

        refs = build_protein_references(
            accession=canonical_acc,
            gene_name=gene_name,
            organism=organism,
            pdb_ids=pdb_ids,
            cross_refs=cross_refs,
        )

        # 3. Upsert into PostgreSQL cache
        try:
            stmt = select(ProteinCache).where(ProteinCache.accession == canonical_acc)
            existing = db.execute(stmt).scalars().first()

            if existing:
                existing.entry_name = entry_name
                existing.protein_name = protein_name
                existing.gene_name = gene_name
                existing.organism = organism
                existing.taxid = taxid
                existing.sequence = sequence
                existing.length = seq_length
                existing.mass = mass_da
                existing.function_summary = function_summary
                existing.subcellular_location = subcellular_loc
                existing.source = "UniProtKB"
                existing.source_data = record
                existing.updated_at = now
            else:
                new_entry = ProteinCache(
                    accession=canonical_acc,
                    entry_name=entry_name,
                    protein_name=protein_name,
                    gene_name=gene_name,
                    organism=organism,
                    taxid=taxid,
                    sequence=sequence,
                    length=seq_length,
                    mass=mass_da,
                    function_summary=function_summary,
                    subcellular_location=subcellular_loc,
                    source="UniProtKB",
                    source_data=record,
                    retrieved_at=now,
                    updated_at=now,
                )
                db.add(new_entry)

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning("Failed to commit protein cache record to PostgreSQL: %s", exc)

        return ProteinDetailResponse(
            accession=canonical_acc,
            entry_name=entry_name,
            protein_name=protein_name,
            gene_name=gene_name,
            organism=organism,
            taxid=taxid,
            sequence_length=seq_length,
            sequence=sequence,
            mass_da=mass_da,
            function_summary=function_summary,
            subcellular_location=subcellular_loc,
            protein_existence=protein_existence,
            ptms=ptms,
            features_summary=feat_summary,
            pdb_structures_count=len(pdb_refs),
            has_alphafold=has_alphafold,
            references=refs,
            source="UniProtKB",
            retrieved_at=now.isoformat(),
            cached=False,
        )

    async def get_sequence(
        self,
        accession: str,
        db: Session,
    ) -> ProteinSequenceAnalysisResponse:
        """Fetch primary sequence and execute computational physicochemical analysis using Biopython."""
        protein = await self.get_protein(accession=accession, db=db)
        return analyze_protein_sequence(
            accession=protein.accession,
            protein_name=protein.protein_name,
            sequence=protein.sequence,
            organism=protein.organism,
        )

    async def get_structures(
        self,
        accession: str,
        db: Session,
    ) -> ProteinStructuresResponse:
        """Retrieve 3D macromolecular structures, contrasting experimental PDB records and AlphaFold AI predictions."""
        protein = await self.get_protein(accession=accession, db=db)

        # Parse experimental PDB structures from cached / upstream record
        cached_data = {}
        stmt = select(ProteinCache).where(ProteinCache.accession == protein.accession)
        cached_row = db.execute(stmt).scalars().first()
        if cached_row and cached_row.source_data:
            cached_data = cached_row.source_data

        cross_refs = cached_data.get("uniProtKBCrossReferences", [])
        pdb_structures = _parse_pdb_crossrefs(cross_refs)

        # Query AlphaFold DB for prediction availability and confidence score
        af_data = await self.client.get_alphafold_prediction(protein.accession)
        predicted_structure: AlphaFoldStructure | None = None

        if af_data:
            plddt = af_data.get("globalMetricValue")
            predicted_structure = AlphaFoldStructure(
                entry_id=str(af_data.get("entryId") or f"AF-{protein.accession}-F1"),
                accession=protein.accession,
                global_plddt=plddt,
                confidence_category=_get_plddt_category(plddt),
                pdb_url=af_data.get("pdbUrl"),
                cif_url=af_data.get("cifUrl"),
                url=f"https://alphafold.ebi.ac.uk/entry/{protein.accession}",
                is_experimental=False,
                prediction_note="Computational AI structure prediction by AlphaFold. Not an experimentally determined structure.",
            )

        return ProteinStructuresResponse(
            accession=protein.accession,
            protein_name=protein.protein_name,
            experimental_structures=pdb_structures,
            predicted_structure=predicted_structure,
            experimental_count=len(pdb_structures),
            predicted_available=predicted_structure is not None,
            source="RCSB PDB & AlphaFold DB via UniProtKB",
        )

    async def get_references(
        self,
        accession: str,
        db: Session,
    ) -> ProteinReferencesResponse:
        """Fetch verified cross-database links and reference URLs for a protein."""
        protein = await self.get_protein(accession=accession, db=db)
        return ProteinReferencesResponse(
            accession=protein.accession,
            protein_name=protein.protein_name,
            references=protein.references,
            source="UniProtKB / RCSB PDB / AlphaFold DB",
        )


# Default shared service instance
protein_service = ProteinService()

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bioinformatics.diseases.client import DiseaseClient
from app.bioinformatics.diseases.schemas import (
    AssociatedTarget,
    DiseaseDetailResponse,
    DiseasePublicationsResponse,
    DiseaseSearchHit,
    DiseaseSearchResponse,
    PublicationHit,
)
from app.models.disease_cache import DiseaseCache

logger = logging.getLogger(__name__)


class DiseaseService:
    """Orchestrates disease searches, Open Targets annotations, caching, and Europe PMC literature."""

    def __init__(self, client: DiseaseClient | None = None) -> None:
        self.client = client or DiseaseClient()

    async def search(self, query: str, size: int = 20) -> DiseaseSearchResponse:
        """Search diseases using Open Targets Platform."""
        total, raw_hits = await self.client.search_diseases(query, size=size)
        hits = [
            DiseaseSearchHit(
                id=h["id"],
                name=h["name"],
                description=h.get("description"),
                entity=h.get("entity", "disease"),
            )
            for h in raw_hits
            if "id" in h and "name" in h
        ]
        return DiseaseSearchResponse(query=query, total=total, results=hits)

    async def get_disease(
        self,
        disease_id: str,
        db: Session,
        force_refresh: bool = False,
    ) -> DiseaseDetailResponse | None:
        """Retrieve disease record with target associations, utilizing PostgreSQL cache."""
        clean_id = disease_id.strip()

        # Check local PostgreSQL cache first
        if not force_refresh:
            cached = db.scalar(
                select(DiseaseCache).where(DiseaseCache.disease_id == clean_id)
            )
            if cached and cached.source_data:
                data = cached.source_data
                return DiseaseDetailResponse(
                    id=cached.disease_id,
                    name=cached.name,
                    description=cached.description,
                    therapeutic_areas=cached.therapeutic_areas or [],
                    synonyms=cached.synonyms or [],
                    source=cached.source,
                    associated_targets=[
                        AssociatedTarget(**t) for t in data.get("associated_targets", [])
                    ],
                    is_cached=True,
                    retrieved_at=cached.retrieved_at,
                )

        # Cold fetch from Open Targets Platform
        raw_disease = await self.client.get_disease_details(clean_id)
        if not raw_disease:
            return None

        # Parse associated targets
        associated_targets: list[AssociatedTarget] = []
        raw_targets = (
            raw_disease.get("associatedTargets", {}).get("rows", [])
            if isinstance(raw_disease.get("associatedTargets"), dict)
            else []
        )
        for row in raw_targets:
            target_data = row.get("target") or {}
            score = float(row.get("score", 0.0))
            associated_targets.append(
                AssociatedTarget(
                    target_id=target_data.get("id", ""),
                    symbol=target_data.get("approvedSymbol", ""),
                    name=target_data.get("approvedName", ""),
                    score=round(score, 4),
                    datatype_scores=row.get("datatypeScores", []),
                )
            )

        therapeutic_areas = [
            {"id": ta.get("id", ""), "name": ta.get("name", "")}
            for ta in (raw_disease.get("therapeuticAreas") or [])
        ]
        synonyms = raw_disease.get("synonyms") or []

        # Update or insert into PostgreSQL cache
        cached_entry = db.scalar(
            select(DiseaseCache).where(DiseaseCache.disease_id == clean_id)
        )
        payload_to_store: dict[str, Any] = {
            "associated_targets": [t.model_dump() for t in associated_targets],
            "raw": raw_disease,
        }

        now = datetime.now(UTC)
        if cached_entry:
            cached_entry.name = raw_disease.get("name", clean_id)
            cached_entry.description = raw_disease.get("description")
            cached_entry.therapeutic_areas = therapeutic_areas
            cached_entry.synonyms = synonyms
            cached_entry.source_data = payload_to_store
            cached_entry.updated_at = now
            db.add(cached_entry)
        else:
            cached_entry = DiseaseCache(
                disease_id=clean_id,
                name=raw_disease.get("name", clean_id),
                description=raw_disease.get("description"),
                therapeutic_areas=therapeutic_areas,
                synonyms=synonyms,
                source="Open Targets Platform",
                source_data=payload_to_store,
                retrieved_at=now,
                updated_at=now,
            )
            db.add(cached_entry)

        try:
            db.commit()
            db.refresh(cached_entry)
        except Exception:
            logger.exception("Failed to commit disease cache for %s", clean_id)
            db.rollback()

        return DiseaseDetailResponse(
            id=clean_id,
            name=cached_entry.name,
            description=cached_entry.description,
            therapeutic_areas=therapeutic_areas,
            synonyms=synonyms,
            source="Open Targets Platform",
            associated_targets=associated_targets,
            is_cached=False,
            retrieved_at=now,
        )

    async def get_publications(
        self,
        disease_id: str,
        disease_name: str,
        size: int = 15,
    ) -> DiseasePublicationsResponse:
        """Fetch scientific publications from Europe PMC matching the disease name."""
        query = f'"{disease_name}" AND (pathology OR genetics OR therapeutic)'
        hit_count, raw_results = await self.client.search_publications(query, page_size=size)

        publications: list[PublicationHit] = []
        for r in raw_results:
            pub_year = None
            if r.get("pubYear"):
                try:
                    pub_year = int(r["pubYear"])
                except ValueError:
                    pass

            publications.append(
                PublicationHit(
                    id=str(r.get("id", "")),
                    title=r.get("title", "Untitled Publication"),
                    authors=r.get("authorString"),
                    journal=r.get("journalTitle"),
                    pub_year=pub_year,
                    pmid=r.get("pmid"),
                    pmcid=r.get("pmcid"),
                    doi=r.get("doi"),
                    cited_by_count=r.get("citedByCount"),
                    source="Europe PMC",
                )
            )

        return DiseasePublicationsResponse(
            disease_id=disease_id,
            disease_name=disease_name,
            query=query,
            total=hit_count,
            publications=publications,
        )

import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class ReactomeConnector(BaseDatabaseConnector):
    """Connector for the Reactome Biological Pathway Knowledgebase."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="reactome",
            name="Reactome",
            description="Open-source curated bioinformatics database of human biological pathways and cellular processes.",
            category=DatabaseCategory.PATHWAYS,
            home_url="https://reactome.org",
            api_docs_url="https://reactome.org/ContentService",
            icon="share-2",
            rate_limit_per_minute=120,
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip()
        url = "https://reactome.org/ContentService/search/query"
        params = {
            "query": clean_q,
            "types": "Pathway",
            "cluster": "true",
        }

        resp = await self._safe_request("GET", url, params=params)
        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if not resp or resp.status_code != 200:
            return ConnectorSearchResult(
                database_id=self.db_id,
                database_name=self.name,
                category=self.category,
                total_hits=0,
                page=page,
                page_size=limit,
                execution_time_ms=exec_ms,
                records=[],
                error=f"Reactome search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        results = data.get("results", [])
        total_hits = 0
        records: list[NormalizedRecord] = []

        # Reactome returns entries clustered by type
        for cluster in results:
            entries = cluster.get("entries", [])
            total_hits += len(entries)
            for entry in entries[:limit]:
                st_id = entry.get("stId", "")
                name = entry.get("name", "Pathway")
                species = entry.get("species", ["Homo sapiens"])[0] if isinstance(entry.get("species"), list) and entry.get("species") else "Homo sapiens"

                records.append(
                    NormalizedRecord(
                        id=st_id,
                        source_database=self.db_id,
                        database_name=self.name,
                        category=self.category,
                        title=name,
                        scientific_name=species,
                        description=f"Biological pathway model. Reactome Stable ID: {st_id}",
                        external_url=f"https://reactome.org/PathwayBrowser/#/{st_id}",
                        metadata={
                            "stId": st_id,
                            "species": species,
                            "is_pathway": True,
                        },
                    )
                )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=total_hits,
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=records[:limit],
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip()
        url = f"https://reactome.org/ContentService/data/query/{clean_id}"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        data: dict[str, Any] = resp.json()
        name = data.get("displayName", clean_id)
        species = data.get("speciesName", "Homo sapiens")

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=name,
            scientific_name=species,
            description=f"Reactome Curated Pathway {clean_id}",
            external_url=f"https://reactome.org/PathwayBrowser/#/{clean_id}",
            metadata=data,
        )

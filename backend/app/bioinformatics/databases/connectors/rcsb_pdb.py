import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class RcsbPdbConnector(BaseDatabaseConnector):
    """Connector for the RCSB Protein Data Bank."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="rcsb_pdb",
            name="RCSB Protein Data Bank",
            description="Authoritative repository for 3D macromolecular structures (X-ray, Cryo-EM, NMR).",
            category=DatabaseCategory.STRUCTURES,
            home_url="https://www.rcsb.org",
            api_docs_url="https://data.rcsb.org",
            icon="layers",
            rate_limit_per_minute=120,
        )

    @property
    def health_url(self) -> str:
        return "https://data.rcsb.org/rest/v1/core/entry/4HHB"

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip()
        if not clean_q:
            return ConnectorSearchResult(
                database_id=self.db_id,
                database_name=self.name,
                category=self.category,
                total_hits=0,
                page=page,
                page_size=limit,
                execution_time_ms=0.0,
                records=[],
            )

        start_row = (page - 1) * limit

        payload = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": clean_q},
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {"start": start_row, "rows": limit},
            },
        }

        resp = await self._safe_request(
            "POST",
            "https://search.rcsb.org/rcsbsearch/v2/query",
            json_data=payload,
        )

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
                error=None if (resp and resp.status_code == 204) else f"RCSB Search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        total_count = data.get("total_count", 0)
        result_set = data.get("result_set", [])

        records: list[NormalizedRecord] = []
        for item in result_set:
            pdb_id = item.get("identifier", "").upper()
            score = item.get("score")
            records.append(
                NormalizedRecord(
                    id=pdb_id,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"PDB {pdb_id}",
                    description=f"Macromolecular crystal structure. Search relevance score: {score:.2f}" if score else "PDB structure entry",
                    external_url=f"https://www.rcsb.org/structure/{pdb_id}",
                    metadata={"pdb_id": pdb_id, "score": score},
                )
            )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=total_count,
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip().upper()
        url = f"https://data.rcsb.org/rest/v1/core/entry/{clean_id}"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        data: dict[str, Any] = resp.json()
        struct_title = data.get("struct", {}).get("title", f"PDB Entry {clean_id}")
        exptl = data.get("exptl", [{}])[0].get("method", "Unknown method")
        res = data.get("rcsb_entry_info", {}).get("resolution_combined", [None])[0]

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"PDB {clean_id}: {struct_title}",
            description=f"Method: {exptl}" + (f", Resolution: {res:.2f} Å" if res else ""),
            external_url=f"https://www.rcsb.org/structure/{clean_id}",
            metadata={
                "pdb_id": clean_id,
                "title": struct_title,
                "experimental_method": exptl,
                "resolution": res,
                "deposit_date": data.get("rcsb_accession_info", {}).get("deposit_date"),
                "release_date": data.get("rcsb_accession_info", {}).get("initial_release_date"),
            },
        )

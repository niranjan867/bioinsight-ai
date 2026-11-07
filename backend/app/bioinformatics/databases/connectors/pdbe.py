import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class PdbeConnector(BaseDatabaseConnector):
    """Connector for the Protein Data Bank in Europe (PDBe)."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="pdbe",
            name="PDBe (Protein Data Bank in Europe)",
            description="European resource for macromolecular structures, validation reports, and ligand interactions.",
            category=DatabaseCategory.STRUCTURES,
            home_url="https://www.ebi.ac.uk/pdbe",
            api_docs_url="https://www.ebi.ac.uk/pdbe/api/doc",
            icon="layers",
            rate_limit_per_minute=120,
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip()
        url = "https://www.ebi.ac.uk/pdbe/search/pdb/select"
        start_row = (page - 1) * limit
        params = {
            "q": clean_q,
            "wt": "json",
            "start": start_row,
            "rows": limit,
            "fl": "pdb_id,title,experimental_method,resolution,organism_name",
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
                error=f"PDBe search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json().get("response", {})
        total_count = data.get("numFound", 0)
        docs = data.get("docs", [])

        records: list[NormalizedRecord] = []
        for doc in docs:
            pdb_id = doc.get("pdb_id", "").upper()
            title = doc.get("title", f"PDBe Structure {pdb_id}")
            method = doc.get("experimental_method", ["Unknown method"])[0] if isinstance(doc.get("experimental_method"), list) else doc.get("experimental_method", "Unknown")
            res = doc.get("resolution")
            orgs = doc.get("organism_name", [])
            org_str = orgs[0] if isinstance(orgs, list) and orgs else None

            records.append(
                NormalizedRecord(
                    id=pdb_id,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"PDBe {pdb_id}: {title}",
                    scientific_name=org_str,
                    description=f"Method: {method}" + (f", Res: {res:.2f} Å" if res else ""),
                    external_url=f"https://www.ebi.ac.uk/pdbe/entry/pdb/{pdb_id}",
                    metadata={
                        "pdb_id": pdb_id,
                        "title": title,
                        "experimental_method": method,
                        "resolution": res,
                    },
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
        clean_id = record_id.strip().lower()
        url = f"https://www.ebi.ac.uk/pdbe/api/pdb/entry/summary/{clean_id}"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        data: dict[str, Any] = resp.json()
        entries = data.get(clean_id, [])
        if not entries:
            return None

        entry = entries[0]
        title = entry.get("title", f"PDB Entry {clean_id.upper()}")
        method = entry.get("experimental_method", ["Unknown"])[0] if isinstance(entry.get("experimental_method"), list) else entry.get("experimental_method")
        res = entry.get("resolution")

        return NormalizedRecord(
            id=clean_id.upper(),
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"PDBe {clean_id.upper()}: {title}",
            description=f"Method: {method}" + (f" | Resolution: {res:.2f} Å" if res else ""),
            external_url=f"https://www.ebi.ac.uk/pdbe/entry/pdb/{clean_id.upper()}",
            metadata={
                "pdb_id": clean_id.upper(),
                "title": title,
                "experimental_method": method,
                "resolution": res,
                "release_date": entry.get("release_date"),
            },
        )

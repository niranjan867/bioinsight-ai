import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class NcbiEntrezConnector(BaseDatabaseConnector):
    """Connector for NCBI Entrez E-utilities (Gene database)."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="ncbi_entrez",
            name="NCBI Entrez (Gene)",
            description="National Center for Biotechnology Information genomic and gene curation database.",
            category=DatabaseCategory.GENES,
            home_url="https://www.ncbi.nlm.nih.gov/gene",
            api_docs_url="https://www.ncbi.nlm.nih.gov/books/NBK25501",
            icon="dna",
            rate_limit_per_minute=180,
        )

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

        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "gene",
            "term": clean_q,
            "retmode": "json",
            "retstart": (page - 1) * limit,
            "retmax": limit,
        }

        s_resp = await self._safe_request("GET", search_url, params=search_params)
        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if not s_resp or s_resp.status_code != 200:
            return ConnectorSearchResult(
                database_id=self.db_id,
                database_name=self.name,
                category=self.category,
                total_hits=0,
                page=page,
                page_size=limit,
                execution_time_ms=exec_ms,
                records=[],
                error=f"NCBI Entrez search failed (HTTP {s_resp.status_code if s_resp else 'No response'})",
            )

        s_data = s_resp.json()
        esearch = s_data.get("esearchresult", {})
        id_list = esearch.get("idlist", [])
        total_count = int(esearch.get("count", len(id_list)))

        if not id_list:
            return ConnectorSearchResult(
                database_id=self.db_id,
                database_name=self.name,
                category=self.category,
                total_hits=0,
                page=page,
                page_size=limit,
                execution_time_ms=exec_ms,
                records=[],
            )

        # Fetch summaries for the retrieved IDs
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "gene",
            "id": ",".join(id_list),
            "retmode": "json",
        }
        sum_resp = await self._safe_request("GET", summary_url, params=summary_params)
        records: list[NormalizedRecord] = []

        if sum_resp and sum_resp.status_code == 200:
            sum_data = sum_resp.json().get("result", {})
            for gene_id in id_list:
                item = sum_data.get(str(gene_id), {})
                name = item.get("name", f"Gene {gene_id}")
                desc = item.get("description", "")
                org = item.get("organism", {}).get("scientificname", "")
                aliases = item.get("otheraliases", "")
                maploc = item.get("maplocation", "")

                records.append(
                    NormalizedRecord(
                        id=str(gene_id),
                        source_database=self.db_id,
                        database_name=self.name,
                        category=self.category,
                        title=f"{name}: {desc}",
                        scientific_name=org,
                        description=f"Aliases: {aliases} | Chromosome Location: {maploc}" if aliases else f"NCBI Gene ID: {gene_id}",
                        external_url=f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}",
                        metadata={
                            "gene_id": gene_id,
                            "symbol": name,
                            "description": desc,
                            "organism": org,
                            "aliases": aliases,
                            "map_location": maploc,
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
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip()
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {"db": "gene", "id": clean_id, "retmode": "json"}
        resp = await self._safe_request("GET", summary_url, params=params)
        if not resp or resp.status_code != 200:
            return None

        sum_data = resp.json().get("result", {})
        item: dict[str, Any] = sum_data.get(str(clean_id), {})
        if not item or "name" not in item:
            return None

        name = item.get("name", "")
        desc = item.get("description", "")
        org = item.get("organism", {}).get("scientificname", "")

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"{name}: {desc}",
            scientific_name=org,
            description=item.get("summary") or f"NCBI Gene entry for {name}",
            external_url=f"https://www.ncbi.nlm.nih.gov/gene/{clean_id}",
            metadata={
                "gene_id": clean_id,
                "symbol": name,
                "description": desc,
                "organism": org,
                "aliases": item.get("otheraliases"),
                "map_location": item.get("maplocation"),
            },
        )

import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class UniprotConnector(BaseDatabaseConnector):
    """Connector for the UniProtKB Protein Knowledgebase."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="uniprot",
            name="UniProtKB",
            description="Comprehensive protein sequence, functional annotation, and structural cross-reference database.",
            category=DatabaseCategory.PROTEINS,
            home_url="https://www.uniprot.org",
            api_docs_url="https://rest.uniprot.org",
            icon="activity",
            rate_limit_per_minute=180,
        )

    @property
    def health_url(self) -> str:
        return "https://rest.uniprot.org/uniprotkb/P68871.json?fields=accession"

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

        url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": clean_q,
            "size": limit,
            "fields": "accession,id,protein_name,gene_names,organism_name,length",
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
                error=f"UniProt search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        results = data.get("results", [])
        total_hits = int(resp.headers.get("x-total-results", len(results)))

        records: list[NormalizedRecord] = []
        for item in results:
            acc = item.get("primaryAccession", "")
            entry_name = item.get("uniProtkbId", "")
            rec_name = (
                item.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("fullName", {})
                .get("value", entry_name)
            )
            organism = item.get("organism", {}).get("scientificName", "")
            genes = [g.get("geneName", {}).get("value") for g in item.get("genes", []) if "geneName" in g]
            gene_str = f" (Gene: {', '.join(filter(None, genes))})" if genes else ""
            length = item.get("sequence", {}).get("length")

            records.append(
                NormalizedRecord(
                    id=acc,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"{rec_name}{gene_str}",
                    scientific_name=organism,
                    description=f"Accession: {acc} | ID: {entry_name} | Length: {length} aa",
                    external_url=f"https://www.uniprot.org/uniprotkb/{acc}/entry",
                    metadata={
                        "accession": acc,
                        "entry_name": entry_name,
                        "organism": organism,
                        "genes": genes,
                        "length": length,
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
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip().upper()
        url = f"https://rest.uniprot.org/uniprotkb/{clean_id}.json"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        data: dict[str, Any] = resp.json()
        acc = data.get("primaryAccession", clean_id)
        rec_name = (
            data.get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value", acc)
        )
        organism = data.get("organism", {}).get("scientificName")
        comments = data.get("comments", [])
        function_text = next(
            (c.get("texts", [{}])[0].get("value") for c in comments if c.get("commentType") == "FUNCTION"),
            None,
        )

        return NormalizedRecord(
            id=acc,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"{rec_name} ({acc})",
            scientific_name=organism,
            description=function_text or f"UniProt protein entry for {acc}",
            external_url=f"https://www.uniprot.org/uniprotkb/{acc}/entry",
            metadata={
                "accession": acc,
                "protein_name": rec_name,
                "organism": organism,
                "function": function_text,
                "sequence_length": data.get("sequence", {}).get("length"),
            },
        )

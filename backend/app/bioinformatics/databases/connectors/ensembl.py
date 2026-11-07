import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class EnsemblConnector(BaseDatabaseConnector):
    """Connector for the Ensembl Genomics REST API."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="ensembl",
            name="Ensembl",
            description="Genomics database providing gene models, genomic annotations, transcripts, and orthologs across species.",
            category=DatabaseCategory.GENES,
            home_url="https://www.ensembl.org",
            api_docs_url="https://rest.ensembl.org",
            icon="dna",
            rate_limit_per_minute=180,
        )

    @property
    def health_url(self) -> str:
        return "https://rest.ensembl.org/info/ping"

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

        url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{clean_q}"
        headers = {"Content-Type": "application/json"}

        resp = await self._safe_request("GET", url, headers=headers)
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
                error=None if (resp and resp.status_code == 400) else f"Ensembl lookup failed ({resp.status_code if resp else 'No response'})",
            )

        gene_data: dict[str, Any] = resp.json()
        ens_id = gene_data.get("id", "")
        display_name = gene_data.get("display_name", clean_q)
        desc = gene_data.get("description", "")
        biotype = gene_data.get("biotype", "")
        seq_region = gene_data.get("seq_region_name", "")
        start_pos = gene_data.get("start")
        end_pos = gene_data.get("end")

        record = NormalizedRecord(
            id=ens_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"{display_name} ({ens_id})",
            scientific_name="Homo sapiens",
            description=f"Biotype: {biotype} | Chr {seq_region}:{start_pos}-{end_pos}. {desc}",
            external_url=f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={ens_id}",
            metadata={
                "ensembl_id": ens_id,
                "display_name": display_name,
                "biotype": biotype,
                "chromosome": seq_region,
                "start": start_pos,
                "end": end_pos,
                "strand": gene_data.get("strand"),
            },
        )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=1,
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=[record],
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip()
        url = f"https://rest.ensembl.org/lookup/id/{clean_id}"
        headers = {"Content-Type": "application/json"}
        resp = await self._safe_request("GET", url, headers=headers)
        if not resp or resp.status_code != 200:
            return None

        data = resp.json()
        display_name = data.get("display_name", clean_id)
        desc = data.get("description", "")

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"{display_name} ({clean_id})",
            scientific_name=data.get("species", "Homo sapiens"),
            description=f"Biotype: {data.get('biotype')} | {desc}",
            external_url=f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={clean_id}",
            metadata=data,
        )

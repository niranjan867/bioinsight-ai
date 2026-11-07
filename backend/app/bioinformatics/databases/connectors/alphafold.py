import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class AlphaFoldConnector(BaseDatabaseConnector):
    """Connector for the DeepMind/EMBL-EBI AlphaFold Protein Structure Database."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="alphafold",
            name="AlphaFold DB",
            description="AI-computed 3D protein structure predictions with residue-level confidence (pLDDT).",
            category=DatabaseCategory.STRUCTURES,
            home_url="https://alphafold.ebi.ac.uk",
            api_docs_url="https://alphafold.ebi.ac.uk/api-docs",
            icon="layers",
            rate_limit_per_minute=120,
        )

    @property
    def health_url(self) -> str:
        return "https://alphafold.ebi.ac.uk/api/prediction/P04637"

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip().upper()
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

        url = f"https://alphafold.ebi.ac.uk/api/prediction/{clean_q}"
        resp = await self._safe_request("GET", url)

        # If direct accession lookup returned 400/404, query UniProt to map gene symbol to accession
        if (not resp or resp.status_code in (400, 404)) and len(clean_q) < 12:
            uniprot_url = "https://rest.uniprot.org/uniprotkb/search"
            u_resp = await self._safe_request(
                "GET",
                uniprot_url,
                params={"query": f"gene_exact:{clean_q} AND organism_id:9606", "size": 1, "fields": "accession"},
            )
            if u_resp and u_resp.status_code == 200:
                results = u_resp.json().get("results", [])
                if results and "primaryAccession" in results[0]:
                    mapped_acc = results[0]["primaryAccession"]
                    url = f"https://alphafold.ebi.ac.uk/api/prediction/{mapped_acc}"
                    resp = await self._safe_request("GET", url)

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
                error=None if (resp and resp.status_code in (400, 404)) else f"AlphaFold lookup failed ({resp.status_code if resp else 'No response'})",
            )

        items: list[dict[str, Any]] = resp.json()
        records: list[NormalizedRecord] = []
        for item in items[:limit]:
            entry_id = item.get("entryId", clean_q)
            uniprot_acc = item.get("uniprotAccession", clean_q)
            gene = item.get("gene", "")
            plddt = item.get("globalMetricValue")
            plddt_str = f" | Global pLDDT: {plddt:.1f}" if plddt is not None else ""

            records.append(
                NormalizedRecord(
                    id=entry_id,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"AlphaFold Model: {uniprot_acc}" + (f" ({gene})" if gene else ""),
                    scientific_name=item.get("organismScientificName"),
                    description=f"Predicted 3D structure for {uniprot_acc}{plddt_str}",
                    external_url=f"https://alphafold.ebi.ac.uk/entry/{uniprot_acc}",
                    metadata={
                        "entry_id": entry_id,
                        "uniprot_accession": uniprot_acc,
                        "plddt": plddt,
                        "pdb_url": item.get("pdbUrl"),
                        "cif_url": item.get("cifUrl"),
                        "sequence_length": item.get("uniprotEnd"),
                    },
                )
            )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=len(items),
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip().upper()
        url = f"https://alphafold.ebi.ac.uk/api/prediction/{clean_id}"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        items = resp.json()
        if not items:
            return None

        item = items[0]
        uniprot_acc = item.get("uniprotAccession", clean_id)
        plddt = item.get("globalMetricValue")

        return NormalizedRecord(
            id=item.get("entryId", clean_id),
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"AlphaFold Model {clean_id}",
            scientific_name=item.get("organismScientificName"),
            description=f"DeepMind computed coordinates for {uniprot_acc}. Global pLDDT: {plddt}",
            external_url=f"https://alphafold.ebi.ac.uk/entry/{uniprot_acc}",
            metadata={
                "pdb_url": item.get("pdbUrl"),
                "cif_url": item.get("cifUrl"),
                "plddt": plddt,
                "uniprot_accession": uniprot_acc,
            },
        )

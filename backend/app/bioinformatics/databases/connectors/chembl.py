import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class ChemblConnector(BaseDatabaseConnector):
    """Connector for the EMBL-EBI ChEMBL Bioactive Database."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="chembl",
            name="ChEMBL",
            description="Manually curated database of bioactive molecules with drug-like properties and therapeutic targets.",
            category=DatabaseCategory.TARGETS,
            home_url="https://www.ebi.ac.uk/chembl",
            api_docs_url="https://www.ebi.ac.uk/chembl/api/data/docs",
            icon="crosshair",
            rate_limit_per_minute=100,
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip()
        offset = (page - 1) * limit
        url = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
        params = {
            "pref_name__icontains": clean_q,
            "limit": limit,
            "offset": offset,
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
                error=f"ChEMBL search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        page_meta = data.get("page_meta", {})
        total_count = page_meta.get("total_count", 0)
        molecules = data.get("molecules", [])

        records: list[NormalizedRecord] = []
        for mol in molecules:
            chembl_id = mol.get("molecule_chembl_id", "")
            pref_name = mol.get("pref_name", chembl_id)
            mol_type = mol.get("molecule_type", "Small molecule")
            max_phase = mol.get("max_phase")
            phase_str = f" | Max Clinical Phase: {max_phase}" if max_phase is not None else ""
            structs = mol.get("molecule_structures") or {}
            smiles = structs.get("canonical_smiles")

            records.append(
                NormalizedRecord(
                    id=chembl_id,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"{pref_name} ({chembl_id})",
                    scientific_name=mol_type,
                    description=f"Type: {mol_type}{phase_str} | ChEMBL bioactive entity",
                    external_url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}",
                    metadata={
                        "chembl_id": chembl_id,
                        "preferred_name": pref_name,
                        "molecule_type": mol_type,
                        "max_phase": max_phase,
                        "canonical_smiles": smiles,
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
        clean_id = record_id.strip().upper()
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{clean_id}.json"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        mol: dict[str, Any] = resp.json()
        chembl_id = mol.get("molecule_chembl_id", clean_id)
        pref_name = mol.get("pref_name", chembl_id)
        mol_type = mol.get("molecule_type", "Small molecule")
        structs = mol.get("molecule_structures") or {}

        return NormalizedRecord(
            id=chembl_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"{pref_name} ({chembl_id})",
            scientific_name=mol_type,
            description=f"ChEMBL Bioactive molecule record for {pref_name}",
            external_url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}",
            metadata={
                "chembl_id": chembl_id,
                "preferred_name": pref_name,
                "molecule_type": mol_type,
                "max_phase": mol.get("max_phase"),
                "canonical_smiles": structs.get("canonical_smiles"),
            },
        )

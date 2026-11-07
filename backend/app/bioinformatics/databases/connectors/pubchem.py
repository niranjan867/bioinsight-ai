import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class PubchemConnector(BaseDatabaseConnector):
    """Connector for NCBI PubChem Compound Database."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="pubchem",
            name="PubChem",
            description="World's largest open chemistry database covering chemical structures, bioactivities, and properties.",
            category=DatabaseCategory.COMPOUNDS,
            home_url="https://pubchem.ncbi.nlm.nih.gov",
            api_docs_url="https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest",
            icon="atom",
            rate_limit_per_minute=100,
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

        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_q}/property/"
            "MolecularFormula,MolecularWeight,IUPACName,InChIKey,IsomericSMILES/JSON"
        )

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
                error=None if (resp and resp.status_code == 404) else f"PubChem query failed ({resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        props_list = data.get("PropertyTable", {}).get("Properties", [])
        records: list[NormalizedRecord] = []

        for prop in props_list[:limit]:
            cid = str(prop.get("CID", ""))
            iupac = prop.get("IUPACName", clean_q.capitalize())
            formula = prop.get("MolecularFormula", "")
            mw = prop.get("MolecularWeight", "")
            smiles = prop.get("IsomericSMILES", "")
            inchikey = prop.get("InChIKey", "")

            records.append(
                NormalizedRecord(
                    id=cid,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=f"{clean_q.capitalize()} (CID: {cid})",
                    scientific_name=iupac,
                    description=f"Formula: {formula} | MW: {mw} g/mol | SMILES: {smiles[:40]}...",
                    external_url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                    metadata={
                        "cid": cid,
                        "iupac_name": iupac,
                        "formula": formula,
                        "molecular_weight": mw,
                        "smiles": smiles,
                        "inchikey": inchikey,
                    },
                )
            )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=len(props_list),
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip()
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{clean_id}/property/"
            "MolecularFormula,MolecularWeight,IUPACName,InChIKey,IsomericSMILES/JSON"
        )
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        props = resp.json().get("PropertyTable", {}).get("Properties", [])
        if not props:
            return None

        prop: dict[str, Any] = props[0]
        cid = str(prop.get("CID", clean_id))
        iupac = prop.get("IUPACName", f"CID {cid}")
        formula = prop.get("MolecularFormula", "")
        mw = prop.get("MolecularWeight", "")
        smiles = prop.get("IsomericSMILES", "")

        return NormalizedRecord(
            id=cid,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=f"Compound CID {cid}",
            scientific_name=iupac,
            description=f"Formula: {formula} | Molecular Weight: {mw} g/mol",
            external_url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            metadata={
                "cid": cid,
                "iupac_name": iupac,
                "formula": formula,
                "molecular_weight": mw,
                "smiles": smiles,
            },
        )

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"


class CompoundClient:
    """Client for PubChem PUG REST and ChEMBL web services."""

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    async def search_by_name(self, name: str, max_records: int = 15) -> list[dict[str, Any]]:
        """Search PubChem by compound name or SMILES and return primary properties."""
        properties = (
            "MolecularWeight,MolecularFormula,ConnectivitySMILES,CanonicalSMILES,"
            "InChIKey,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,Title"
        )
        url = f"{PUBCHEM_BASE_URL}/compound/name/{name}/property/{properties}/JSON"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params={"MaxRecords": max_records})
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                return data.get("PropertyTable", {}).get("Properties", [])
            except httpx.HTTPError as exc:
                logger.warning("PubChem search failed for '%s': %s", name, exc)
                return []

    async def get_by_cid(self, cid: int) -> dict[str, Any] | None:
        """Fetch complete molecular properties for a given PubChem CID."""
        properties = (
            "MolecularWeight,MolecularFormula,CanonicalSMILES,IsomericSMILES,ConnectivitySMILES,"
            "InChI,InChIKey,IUPACName,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
            "RotatableBondCount,ExactMass,Title"
        )
        url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/property/{properties}/JSON"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                props = response.json().get("PropertyTable", {}).get("Properties", [])
                return props[0] if props else None
            except httpx.HTTPError as exc:
                logger.warning("PubChem properties query failed for CID %d: %s", cid, exc)
                return None

    async def get_synonyms(self, cid: int) -> list[str]:
        """Fetch popular synonyms or brand names for a CID."""
        url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/synonyms/JSON"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    return []
                data = response.json()
                info = data.get("InformationList", {}).get("Information", [])
                return info[0].get("Synonym", [])[:10] if info else []
            except (httpx.HTTPError, ValueError, KeyError):
                return []

    async def get_3d_sdf(self, cid: int) -> str | None:
        """Download 3D conformer coordinates in SDF format."""
        url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/SDF"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params={"record_type": "3d"})
                if response.status_code == 200:
                    return response.text
                # Fallback to 2D SDF if 3D conformer not yet calculated
                fallback = await client.get(url, params={"record_type": "2d"})
                if fallback.status_code == 200:
                    return fallback.text
                return None
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                logger.warning("Failed to fetch SDF for CID %d: %s", cid, exc)
                return None

    async def find_chembl_molecule_by_inchi_key(self, inchi_key: str) -> str | None:
        """Find ChEMBL molecule ID using InChIKey."""
        url = f"{CHEMBL_BASE_URL}/molecule/{inchi_key}.json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json().get("molecule_chembl_id")
                return None
            except (httpx.HTTPError, ValueError, KeyError):
                return None

    async def get_chembl_mechanisms(self, chembl_id: str) -> list[dict[str, Any]]:
        """Retrieve mechanism of action and target records from ChEMBL."""
        url = f"{CHEMBL_BASE_URL}/mechanism.json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params={"molecule_chembl_id": chembl_id})
                if response.status_code != 200:
                    return []
                data = response.json()
                return data.get("mechanisms", [])
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                logger.warning("Failed to fetch ChEMBL mechanisms for %s: %s", chembl_id, exc)
                return []

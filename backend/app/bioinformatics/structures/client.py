import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RCSB_DATA_URL = "https://data.rcsb.org/rest/v1/core/entry"
RCSB_FILES_URL = "https://files.rcsb.org/download"
ALPHAFOLD_API_URL = "https://alphafold.ebi.ac.uk/api/prediction"


class StructureClient:
    """HTTP client for querying RCSB Protein Data Bank and AlphaFold DB."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def get_rcsb_entry(self, pdb_id: str) -> dict[str, Any] | None:
        """Fetch experimental entry metadata from RCSB PDB."""
        clean_id = pdb_id.strip().upper()
        url = f"{RCSB_DATA_URL}/{clean_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                logger.warning("RCSB entry query failed for %s: %s", clean_id, exc)
                return None

    async def get_rcsb_pdb_text(self, pdb_id: str) -> str | None:
        """Download raw atomic coordinate PDB file from RCSB PDB."""
        clean_id = pdb_id.strip().upper()
        url = f"{RCSB_FILES_URL}/{clean_id}.pdb"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as exc:
                logger.warning("RCSB PDB download failed for %s: %s", clean_id, exc)
                return None

    async def get_alphafold_prediction(self, accession: str) -> dict[str, Any] | None:
        """Fetch AlphaFold DB predicted structure entry for a UniProt accession."""
        clean_acc = accession.strip().upper()
        url = f"{ALPHAFOLD_API_URL}/{clean_acc}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return data[0] if isinstance(data, list) and data else None
            except httpx.HTTPError as exc:
                logger.warning("AlphaFold DB query failed for %s: %s", clean_acc, exc)
                return None

    async def get_alphafold_pdb_text(self, pdb_url: str) -> str | None:
        """Download predicted coordinates PDB file from AlphaFold DB."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(pdb_url)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as exc:
                logger.warning("AlphaFold PDB file download failed: %s", exc)
                return None

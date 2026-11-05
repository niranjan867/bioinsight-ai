import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

UNIPROT_BASE_URL = "https://rest.uniprot.org"
ALPHAFOLD_BASE_URL = "https://alphafold.ebi.ac.uk/api"
RCSB_PDB_BASE_URL = "https://data.rcsb.org/rest/v1"

DEFAULT_TIMEOUT = 8.0
MAX_RETRIES = 2
RETRY_STATUS_CODES = {502, 503, 504}


class ProteinClientError(Exception):
    """Base exception for Protein Intelligence external API communication."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class ProteinNotFoundError(ProteinClientError):
    """Raised when an inspected protein is not cataloged in external biological databases."""

    def __init__(self, accession: str):
        super().__init__(f"Protein '{accession}' not found in UniProtKB", status_code=404)
        self.accession = accession


class ProteinApiClient:
    """Asynchronous client for UniProtKB, AlphaFold DB, and RCSB PDB APIs with retry resilience."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def _execute_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute GET request with exponential backoff on transient gateway errors."""
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.get(url, params=params)
                if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                    backoff = 0.5 * (2**attempt)
                    logger.warning(
                        "Upstream %s returned HTTP %d on attempt %d. Retrying in %.2fs",
                        url,
                        response.status_code,
                        attempt + 1,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exception = exc
                if attempt < MAX_RETRIES:
                    backoff = 0.5 * (2**attempt)
                    logger.warning(
                        "Network error connecting to %s on attempt %d: %s. Retrying in %.2fs",
                        url,
                        attempt + 1,
                        exc,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                break

        raise ProteinClientError(
            f"Failed to communicate with biological service at {url}: {last_exception}",
            status_code=504 if isinstance(last_exception, httpx.TimeoutException) else 502,
        )

    async def search_uniprot(
        self,
        query: str,
        taxid: int | None = None,
        limit: int = 15,
    ) -> dict[str, Any]:
        """Search UniProtKB entries by keyword, gene symbol, or protein name."""
        clean_query = query.strip()
        formatted_query = f"({clean_query})"
        if taxid:
            formatted_query = f"{formatted_query} AND (organism_id:{taxid})"

        params = {
            "query": formatted_query,
            "size": min(max(limit, 1), 50),
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{UNIPROT_BASE_URL}/uniprotkb/search",
                    params=params,
                )
            except Exception as e:
                if isinstance(e, ProteinClientError):
                    raise
                raise ProteinClientError(f"Failed to query UniProtKB: {e}") from e

            if resp.status_code == 404:
                return {"results": [], "total": 0}

            if not resp.is_success:
                logger.warning("UniProtKB search returned status %d: %s", resp.status_code, resp.text)
                raise ProteinClientError(
                    f"UniProtKB search service returned HTTP {resp.status_code}",
                    status_code=502,
                )

            try:
                data = resp.json()
                total_header = resp.headers.get("x-total-results")
                total = int(total_header) if total_header and total_header.isdigit() else len(data.get("results", []))
                data["total"] = total
                return data
            except (ValueError, TypeError) as exc:
                raise ProteinClientError("Failed to parse UniProtKB JSON response", status_code=502) from exc

    async def get_uniprot_entry(self, accession: str) -> dict[str, Any]:
        """Fetch comprehensive biological protein record from UniProtKB."""
        clean_acc = accession.strip().upper()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{UNIPROT_BASE_URL}/uniprotkb/{clean_acc}.json",
                )
            except Exception as e:
                if isinstance(e, ProteinClientError):
                    raise
                raise ProteinClientError(f"Failed to contact UniProtKB for '{clean_acc}': {e}") from e

            if resp.status_code == 404:
                raise ProteinNotFoundError(clean_acc)

            if not resp.is_success:
                raise ProteinClientError(
                    f"UniProtKB returned HTTP {resp.status_code}",
                    status_code=502,
                )

            try:
                return resp.json()
            except (ValueError, TypeError) as exc:
                raise ProteinClientError("Failed to parse UniProtKB JSON record", status_code=502) from exc

    async def get_alphafold_prediction(self, accession: str) -> dict[str, Any] | None:
        """Fetch AlphaFold protein structure prediction metadata."""
        clean_acc = accession.strip().upper()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{ALPHAFOLD_BASE_URL}/prediction/{clean_acc}",
                )
                if not resp.is_success:
                    return None

                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return None
            except (httpx.HTTPError, ValueError, ProteinClientError) as exc:
                logger.info("Optional AlphaFold prediction fetch skipped for '%s': %s", clean_acc, exc)
                return None

    async def get_rcsb_entry(self, pdb_id: str) -> dict[str, Any] | None:
        """Fetch RCSB Protein Data Bank core entry metadata."""
        clean_pdb = pdb_id.strip().upper()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{RCSB_PDB_BASE_URL}/core/entry/{clean_pdb}",
                )
                if not resp.is_success:
                    return None
                return resp.json()
            except (httpx.HTTPError, ValueError, ProteinClientError) as exc:
                logger.info("Optional RCSB PDB metadata fetch skipped for '%s': %s", clean_pdb, exc)
                return None


# Default shared client instance
protein_client = ProteinApiClient()


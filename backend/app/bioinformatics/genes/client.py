import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MYGENE_BASE_URL = "https://mygene.info/v3"
NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

DEFAULT_TIMEOUT = 8.0
MAX_RETRIES = 2
RETRY_STATUS_CODES = {502, 503, 504}


class GeneClientError(Exception):
    """Base exception for Gene Intelligence external API communication."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GeneNotFoundError(GeneClientError):
    """Raised when an inspected gene is not present in external biological databases."""

    def __init__(self, gene_id: str):
        super().__init__(f"Gene '{gene_id}' not found in biological databases", status_code=404)
        self.gene_id = gene_id


class GeneApiClient:
    """Asynchronous client for MyGene.info and NCBI Entrez APIs with resilience and rate-limit handling."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def _execute_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute GET request with exponential backoff on transient errors."""
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.get(url, params=params)
                if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                return response
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                last_exception = exc
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                break

        logger.error("External gene API request failed after %d retries: %s", MAX_RETRIES, url)
        raise GeneClientError(
            f"External bioinformatics API unavailable: {last_exception or 'Request timed out'}",
            status_code=504,
        )

    async def search_mygene(
        self,
        query: str,
        species: str = "human",
        limit: int = 15,
    ) -> dict[str, Any]:
        """Query MyGene.info search API for genes matching query."""
        fields = (
            "symbol,name,taxid,entrezgene,ensembl.gene,"
            "genomic_pos,summary,alias,type_of_gene"
        )
        params: dict[str, Any] = {
            "q": query,
            "size": min(max(1, limit), 50),
            "fields": fields,
        }
        if species and species.lower() != "all":
            params["species"] = species.lower()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{MYGENE_BASE_URL}/query",
                    params=params,
                )
            except Exception as e:
                if isinstance(e, GeneClientError):
                    raise
                raise GeneClientError(f"Failed to query MyGene.info: {e}") from e

            if resp.status_code == 404:
                return {"hits": [], "total": 0}

            if not resp.is_success:
                logger.warning("MyGene search returned status %d: %s", resp.status_code, resp.text)
                raise GeneClientError(
                    f"MyGene search service error: HTTP {resp.status_code}",
                    status_code=502,
                )

            try:
                return resp.json()
            except Exception as exc:
                raise GeneClientError("Failed to parse MyGene.info JSON response", status_code=502) from exc

    async def get_mygene_record(self, gene_id: str) -> dict[str, Any]:
        """Fetch comprehensive gene record from MyGene.info."""
        fields = (
            "symbol,name,taxid,entrezgene,ensembl,genomic_pos,"
            "summary,alias,type_of_gene,refseq"
        )
        params = {"fields": fields}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{MYGENE_BASE_URL}/gene/{gene_id}",
                    params=params,
                )
            except Exception as e:
                if isinstance(e, GeneClientError):
                    raise
                raise GeneClientError(f"Failed to contact MyGene.info: {e}") from e

            if resp.status_code == 404:
                # If gene_id is a symbol (not an Entrez numeric ID), attempt symbol resolution
                if not gene_id.isdigit():
                    resolved_id = await self._resolve_symbol_to_id(gene_id)
                    if resolved_id and resolved_id != gene_id:
                        return await self.get_mygene_record(resolved_id)
                raise GeneNotFoundError(gene_id)

            if not resp.is_success:
                raise GeneClientError(
                    f"MyGene.info returned HTTP {resp.status_code}",
                    status_code=502,
                )

            try:
                data = resp.json()
            except Exception as exc:
                raise GeneClientError("Failed to parse MyGene record JSON", status_code=502) from exc

            if data.get("notfound") is True:
                if not gene_id.isdigit():
                    resolved_id = await self._resolve_symbol_to_id(gene_id)
                    if resolved_id and resolved_id != gene_id:
                        return await self.get_mygene_record(resolved_id)
                raise GeneNotFoundError(gene_id)

            return data

    async def _resolve_symbol_to_id(self, symbol: str) -> str | None:
        """Resolve a gene symbol or synonym to its primary biological Entrez ID."""
        try:
            search_res = await self.search_mygene(query=symbol, limit=5)
            hits = search_res.get("hits", [])
            for hit in hits:
                hit_sym = str(hit.get("symbol") or "")
                if hit_sym.upper() == symbol.upper():
                    return str(hit.get("_id") or hit.get("entrezgene"))
        except (httpx.HTTPError, ValueError, GeneClientError) as exc:
            logger.info("Symbol resolution fallback skipped for '%s': %s", symbol, exc)
        return None

    async def get_ncbi_summary(self, entrez_id: str) -> dict[str, Any] | None:
        """Fetch NCBI Entrez Gene summary as secondary authoritative source."""
        params = {
            "db": "gene",
            "id": entrez_id,
            "retmode": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await self._execute_with_retry(
                    client,
                    f"{NCBI_EUTILS_BASE_URL}/esummary.fcgi",
                    params=params,
                )
                if not resp.is_success:
                    return None

                data = resp.json()
                result = data.get("result", {})
                uid_data = result.get(str(entrez_id))
                if isinstance(uid_data, dict):
                    return uid_data
                return None
            except (httpx.HTTPError, ValueError, GeneClientError) as exc:
                logger.info("Optional NCBI summary fetch skipped: %s", exc)
                return None


# Default shared client instance
gene_client = GeneApiClient()

import abc
import asyncio
import logging
import time
from typing import Any

import httpx

from app.bioinformatics.databases.schemas import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)

logger = logging.getLogger(__name__)


class BaseDatabaseConnector(abc.ABC):
    """Abstract base class for all scientific database connectors."""

    def __init__(
        self,
        timeout: float = 12.0,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    @property
    @abc.abstractmethod
    def metadata(self) -> ConnectorMetadata:
        """Connector metadata including id, name, description, and URLs."""
        ...

    @property
    def db_id(self) -> str:
        return self.metadata.id

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def category(self) -> DatabaseCategory:
        return self.metadata.category

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 10,
    ) -> ConnectorSearchResult:
        """Search the database and return normalized records."""
        ...

    @abc.abstractmethod
    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        """Retrieve a specific record by its primary database identifier."""
        ...

    @property
    def health_url(self) -> str:
        """Endpoint to check for service health. Defaults to home_url."""
        return self.metadata.home_url

    async def check_health(self) -> ConnectorHealthStatus:
        """Verify endpoint connectivity and measure response latency."""
        start = time.perf_counter()
        headers = {"User-Agent": "BioInsight-AI/2.0 (bioinformatics-platform)"}
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=8.0),
                follow_redirects=True,
                headers=headers,
            ) as client:
                res = await client.get(self.health_url)
                latency = round((time.perf_counter() - start) * 1000, 2)
                is_healthy = res.status_code < 400
                return ConnectorHealthStatus(
                    database_id=self.db_id,
                    name=self.name,
                    is_healthy=is_healthy,
                    latency_ms=latency,
                    status_code=res.status_code,
                    message="Available" if is_healthy else f"HTTP {res.status_code}",
                )
        except Exception as exc:  # noqa: BLE001
            latency = round((time.perf_counter() - start) * 1000, 2)
            logger.warning("Health check failed for %s: %s", self.name, exc)
            return ConnectorHealthStatus(
                database_id=self.db_id,
                name=self.name,
                is_healthy=False,
                latency_ms=latency,
                message=str(exc),
            )

    async def _safe_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | None:
        """Execute HTTP request with retry logic and exponential backoff."""
        req_headers = {"User-Agent": "BioInsight-AI/2.0 (bioinformatics-platform)"}
        if headers:
            req_headers.update(headers)

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                    follow_redirects=True,
                ) as client:
                    if method.upper() == "POST":
                        response = await client.post(url, params=params, json=json_data, headers=req_headers)
                    else:
                        response = await client.get(url, params=params, headers=req_headers)

                    if response.status_code == 429:
                        # Rate limit hit: backoff and retry
                        delay = self.backoff_factor * (2**attempt)
                        logger.warning("%s rate limited (429). Retrying in %.2fs", self.name, delay)
                        await asyncio.sleep(delay)
                        continue

                    if response.status_code in (500, 502, 503, 504) and attempt < self.max_retries:
                        delay = self.backoff_factor * (2**attempt)
                        logger.warning("%s server error (%d). Retrying in %.2fs", self.name, response.status_code, delay)
                        await asyncio.sleep(delay)
                        continue

                    return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self.max_retries:
                    delay = self.backoff_factor * (2**attempt)
                    logger.warning("%s request error (%s). Retrying in %.2fs", self.name, exc, delay)
                    await asyncio.sleep(delay)
                else:
                    logger.warning("%s request failed after %d attempts: %s", self.name, self.max_retries + 1, exc)
                    return None
            except Exception as exc:  # noqa: BLE001
                logger.error("%s unexpected error during request: %s", self.name, exc)
                return None
        return None

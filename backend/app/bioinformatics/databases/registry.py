import asyncio
import logging
import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.connectors import (
    AlphaFoldConnector,
    ChemblConnector,
    EnsemblConnector,
    EuropePmcConnector,
    NcbiEntrezConnector,
    OpenTargetsConnector,
    PdbeConnector,
    PubchemConnector,
    RcsbPdbConnector,
    ReactomeConnector,
    UniprotConnector,
)
from app.bioinformatics.databases.schemas import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    GlobalSearchRequest,
    GlobalSearchResponse,
    NormalizedRecord,
)

logger = logging.getLogger(__name__)


class DatabaseRegistry:
    """Registry and orchestrator for all scientific database connectors."""

    def __init__(self) -> None:
        self._connectors: dict[str, BaseDatabaseConnector] = {}
        self._register_default_connectors()

    def register(self, connector: BaseDatabaseConnector) -> None:
        """Register a new scientific database connector."""
        self._connectors[connector.db_id] = connector
        logger.info("Registered database connector: %s (%s)", connector.name, connector.db_id)

    def get_connector(self, db_id: str) -> BaseDatabaseConnector | None:
        return self._connectors.get(db_id)

    def list_connectors(self) -> list[ConnectorMetadata]:
        return [c.metadata for c in self._connectors.values()]

    def list_by_category(self, category: DatabaseCategory) -> list[BaseDatabaseConnector]:
        return [c for c in self._connectors.values() if c.category == category]

    def _register_default_connectors(self) -> None:
        """Register the 11 authoritative scientific connectors."""
        self.register(RcsbPdbConnector())
        self.register(UniprotConnector())
        self.register(PubchemConnector())
        self.register(NcbiEntrezConnector())
        self.register(PdbeConnector())
        self.register(AlphaFoldConnector())
        self.register(ChemblConnector())
        self.register(EuropePmcConnector())
        self.register(OpenTargetsConnector())
        self.register(EnsemblConnector())
        self.register(ReactomeConnector())

    async def search_all(self, request: GlobalSearchRequest) -> GlobalSearchResponse:
        """Execute parallel search across enabled connectors with partial failure handling."""
        start_time = time.perf_counter()

        # Filter connectors by requested databases or categories
        target_connectors: list[BaseDatabaseConnector] = []
        for c in self._connectors.values():
            if request.databases and c.db_id not in request.databases:
                continue
            if request.categories and c.category not in request.categories:
                continue
            target_connectors.append(c)

        if not target_connectors:
            return GlobalSearchResponse(
                query=request.query,
                total_results=0,
                execution_time_ms=0.0,
                categories_found=[],
                results_by_category={},
                database_statuses=[],
            )

        # Execute searches concurrently
        tasks = [
            c.search(request.query, page=request.page, limit=request.limit)
            for c in target_connectors
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        results_by_category: dict[str, list[NormalizedRecord]] = {}
        database_statuses: list[dict[str, Any]] = []
        total_results = 0

        for connector, res in zip(target_connectors, results, strict=False):
            if isinstance(res, Exception):
                logger.warning("Connector %s failed with exception: %s", connector.name, res)
                database_statuses.append({
                    "database_id": connector.db_id,
                    "database_name": connector.name,
                    "status": "failed",
                    "error": str(res),
                    "hits": 0,
                })
            elif isinstance(res, ConnectorSearchResult):
                status_str = "failed" if res.error and not res.records else "ok"
                database_statuses.append({
                    "database_id": res.database_id,
                    "database_name": res.database_name,
                    "status": status_str,
                    "error": res.error,
                    "hits": len(res.records),
                    "total_hits": res.total_hits,
                    "execution_time_ms": res.execution_time_ms,
                })

                for rec in res.records:
                    cat_key = rec.category.value
                    if cat_key not in results_by_category:
                        results_by_category[cat_key] = []
                    results_by_category[cat_key].append(rec)
                    total_results += 1

        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)
        categories_found = sorted(results_by_category.keys())

        return GlobalSearchResponse(
            query=request.query,
            total_results=total_results,
            execution_time_ms=exec_ms,
            categories_found=categories_found,
            results_by_category=results_by_category,
            database_statuses=database_statuses,
        )

    async def check_all_health(self) -> list[ConnectorHealthStatus]:
        """Perform concurrent health checks across all registered connectors."""
        tasks = [c.check_health() for c in self._connectors.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        statuses: list[ConnectorHealthStatus] = []
        for connector, res in zip(self._connectors.values(), results, strict=False):
            if isinstance(res, Exception):
                statuses.append(
                    ConnectorHealthStatus(
                        database_id=connector.db_id,
                        name=connector.name,
                        is_healthy=False,
                        latency_ms=0.0,
                        message=str(res),
                    )
                )
            elif isinstance(res, ConnectorHealthStatus):
                statuses.append(res)
        return statuses


# Global singleton instance
registry = DatabaseRegistry()

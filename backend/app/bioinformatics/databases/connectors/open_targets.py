import time

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class OpenTargetsConnector(BaseDatabaseConnector):
    """Connector for the Open Targets Platform API."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="open_targets",
            name="Open Targets Platform",
            description="Systematic identification and prioritization of disease drug targets using human genetics and genomics.",
            category=DatabaseCategory.TARGETS,
            home_url="https://platform.opentargets.org",
            api_docs_url="https://platform-docs.opentargets.org/data-access/graphql-api",
            icon="crosshair",
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

        graphql_query = """
        query SearchTarget($q: String!) {
            search(queryString: $q, entityNames: ["target", "disease"]) {
                total
                hits {
                    id
                    name
                    description
                    entity
                }
            }
        }
        """
        payload = {"query": graphql_query, "variables": {"q": clean_q}}
        resp = await self._safe_request(
            "POST",
            "https://api.platform.opentargets.org/api/v4/graphql",
            json_data=payload,
        )

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
                error=f"Open Targets query failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json().get("data", {}).get("search", {})
        total_count = data.get("total", 0)
        hits = data.get("hits", [])

        records: list[NormalizedRecord] = []
        for hit in hits[:limit]:
            target_id = hit.get("id", "")
            name = hit.get("name", target_id)
            desc = hit.get("description", "")
            entity = hit.get("entity", "target")
            cat = DatabaseCategory.DISEASES if entity == "disease" else DatabaseCategory.TARGETS

            records.append(
                NormalizedRecord(
                    id=target_id,
                    source_database=self.db_id,
                    database_name=self.name,
                    category=cat,
                    title=f"{name} ({target_id})",
                    scientific_name=f"Entity: {entity.capitalize()}",
                    description=desc or f"Open Targets {entity} record for {name}",
                    external_url=f"https://platform.opentargets.org/{entity}/{target_id}",
                    metadata={
                        "target_id": target_id,
                        "name": name,
                        "entity": entity,
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
        clean_id = record_id.strip()
        graphql_query = """
        query TargetDetail($id: String!) {
            target(ensemblId: $id) {
                id
                approvedSymbol
                approvedName
                functionDescriptions
                biotype
            }
        }
        """
        payload = {"query": graphql_query, "variables": {"id": clean_id}}
        resp = await self._safe_request(
            "POST",
            "https://api.platform.opentargets.org/api/v4/graphql",
            json_data=payload,
        )
        if not resp or resp.status_code != 200:
            return None

        target = resp.json().get("data", {}).get("target")
        if not target:
            return None

        sym = target.get("approvedSymbol", clean_id)
        name = target.get("approvedName", sym)
        funcs = target.get("functionDescriptions", [])
        desc = funcs[0] if funcs else f"Biotype: {target.get('biotype')}"

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=DatabaseCategory.TARGETS,
            title=f"{sym}: {name}",
            scientific_name=f"Biotype: {target.get('biotype')}",
            description=desc,
            external_url=f"https://platform.opentargets.org/target/{clean_id}",
            metadata=target,
        )

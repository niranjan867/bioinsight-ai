import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENTARGETS_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class DiseaseClient:
    """HTTP client for querying Open Targets Platform and Europe PMC literature APIs."""

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    async def search_diseases(self, query: str, size: int = 20) -> tuple[int, list[dict[str, Any]]]:
        """Search diseases across Open Targets Platform."""
        graphql_query = """
        query SearchDiseases($queryString: String!, $size: Int!) {
            search(queryString: $queryString, entityNames: ["disease"], page: {index: 0, size: $size}) {
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
        payload = {
            "query": graphql_query,
            "variables": {
                "queryString": query,
                "size": size,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(OPENTARGETS_GRAPHQL_URL, json=payload)
                response.raise_for_status()
                data = response.json()
                search_data = data.get("data", {}).get("search", {})
                total = search_data.get("total", 0)
                hits = search_data.get("hits", [])
                return total, hits
            except httpx.HTTPError as exc:
                logger.warning("Open Targets disease search failed: %s", exc)
                return 0, []

    async def get_disease_details(self, efo_id: str) -> dict[str, Any] | None:
        """Fetch disease metadata and associated targets from Open Targets Platform."""
        graphql_query = """
        query DiseaseDetails($efoId: String!) {
            disease(efoId: $efoId) {
                id
                name
                description
                synonyms
                therapeuticAreas {
                    id
                    name
                }
                associatedTargets(page: {size: 30}) {
                    count
                    rows {
                        score
                        datatypeScores {
                            id
                            score
                        }
                        target {
                            id
                            approvedSymbol
                            approvedName
                        }
                    }
                }
            }
        }
        """
        payload = {
            "query": graphql_query,
            "variables": {"efoId": efo_id},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(OPENTARGETS_GRAPHQL_URL, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("disease")
            except httpx.HTTPError as exc:
                logger.warning("Open Targets disease details query failed for %s: %s", efo_id, exc)
                return None

    async def search_publications(
        self, query: str, page_size: int = 15
    ) -> tuple[int, list[dict[str, Any]]]:
        """Query Europe PMC for peer-reviewed literature associated with disease or target."""
        params = {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "resultType": "lite",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(EUROPE_PMC_SEARCH_URL, params=params)
                response.raise_for_status()
                data = response.json()
                result_list = data.get("resultList", {}).get("result", [])
                hit_count = data.get("hitCount", 0)
                return hit_count, result_list
            except httpx.HTTPError as exc:
                logger.warning("Europe PMC search failed for '%s': %s", query, exc)
                return 0, []


import time
from typing import Any

from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    NormalizedRecord,
)


class EuropePmcConnector(BaseDatabaseConnector):
    """Connector for the Europe PMC biomedical literature repository."""

    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="europe_pmc",
            name="Europe PMC",
            description="Open-access repository of millions of biomedical and life sciences research publications and preprints.",
            category=DatabaseCategory.PUBLICATIONS,
            home_url="https://europepmc.org",
            api_docs_url="https://europepmc.org/RestfulWebService",
            icon="file-text",
            rate_limit_per_minute=180,
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        start_time = time.perf_counter()
        clean_q = query.strip()
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {
            "query": clean_q,
            "format": "json",
            "pageSize": limit,
            "resultType": "core",
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
                error=f"Europe PMC search failed (HTTP {resp.status_code if resp else 'No response'})",
            )

        data = resp.json()
        total_hits = data.get("hitCount", 0)
        result_list = data.get("resultList", {}).get("result", [])

        records: list[NormalizedRecord] = []
        for pub in result_list:
            pmid = pub.get("pmid") or pub.get("id", "")
            title = pub.get("title", "Untitled Publication").rstrip(".")
            author_str = pub.get("authorString", "")
            journal = pub.get("journalTitle") or pub.get("journalInfo", {}).get("journal", {}).get("title", "")
            pub_year = pub.get("pubYear", "")
            doi = pub.get("doi", "")
            abstract = pub.get("abstractText", "")
            short_abstract = abstract[:200] + "..." if len(abstract) > 200 else abstract

            records.append(
                NormalizedRecord(
                    id=str(pmid),
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title=title,
                    scientific_name=author_str[:100] + ("..." if len(author_str) > 100 else ""),
                    description=f"{journal} ({pub_year}). {short_abstract}" if short_abstract else f"{journal} ({pub_year})",
                    external_url=f"https://europepmc.org/article/MED/{pmid}" if pmid else f"https://doi.org/{doi}",
                    metadata={
                        "pmid": pmid,
                        "doi": doi,
                        "journal": journal,
                        "pub_year": pub_year,
                        "cited_by_count": pub.get("citedByCount"),
                    },
                )
            )

        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=total_hits,
            page=page,
            page_size=limit,
            execution_time_ms=exec_ms,
            records=records,
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        clean_id = record_id.strip()
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=ext_id:{clean_id}%20src:med&format=json&resultType=core"
        resp = await self._safe_request("GET", url)
        if not resp or resp.status_code != 200:
            return None

        results = resp.json().get("resultList", {}).get("result", [])
        if not results:
            return None

        pub: dict[str, Any] = results[0]
        title = pub.get("title", "Untitled Publication")
        journal = pub.get("journalTitle", "")
        year = pub.get("pubYear", "")

        return NormalizedRecord(
            id=clean_id,
            source_database=self.db_id,
            database_name=self.name,
            category=self.category,
            title=title,
            scientific_name=pub.get("authorString"),
            description=pub.get("abstractText") or f"{journal} ({year})",
            external_url=f"https://europepmc.org/article/MED/{clean_id}",
            metadata={
                "pmid": clean_id,
                "doi": pub.get("doi"),
                "journal": journal,
                "pub_year": year,
            },
        )

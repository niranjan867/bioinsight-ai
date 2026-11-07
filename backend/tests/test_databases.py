from unittest.mock import AsyncMock, patch

import pytest
from app.bioinformatics.databases.base import BaseDatabaseConnector
from app.bioinformatics.databases.registry import DatabaseRegistry
from app.bioinformatics.databases.schemas import (
    ConnectorMetadata,
    ConnectorSearchResult,
    DatabaseCategory,
    GlobalSearchRequest,
    NormalizedRecord,
)
from app.main import app
from fastapi.testclient import TestClient


class DummyFailingConnector(BaseDatabaseConnector):
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="dummy_fail",
            name="Failing DB",
            description="Simulates network outage",
            category=DatabaseCategory.GENES,
            home_url="https://fail.example.org",
            api_docs_url="https://fail.example.org/docs",
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        msg = "Simulated upstream 503 error"
        raise RuntimeError(msg)

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        return None


class DummySuccessConnector(BaseDatabaseConnector):
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="dummy_success",
            name="Success DB",
            description="Simulates healthy response",
            category=DatabaseCategory.PROTEINS,
            home_url="https://success.example.org",
            api_docs_url="https://success.example.org/docs",
        )

    async def search(self, query: str, page: int = 1, limit: int = 10) -> ConnectorSearchResult:
        return ConnectorSearchResult(
            database_id=self.db_id,
            database_name=self.name,
            category=self.category,
            total_hits=1,
            records=[
                NormalizedRecord(
                    id="REC123",
                    source_database=self.db_id,
                    database_name=self.name,
                    category=self.category,
                    title="Dummy Protein Record",
                    external_url="https://success.example.org/REC123",
                )
            ],
        )

    async def get_record(self, record_id: str) -> NormalizedRecord | None:
        if record_id == "REC123":
            return NormalizedRecord(
                id="REC123",
                source_database=self.db_id,
                database_name=self.name,
                category=self.category,
                title="Dummy Protein Record",
                external_url="https://success.example.org/REC123",
            )
        return None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_registry_contains_11_core_databases() -> None:
    reg = DatabaseRegistry()
    connectors = reg.list_connectors()
    assert len(connectors) == 11

    expected_ids = {
        "rcsb_pdb",
        "uniprot",
        "pubchem",
        "ncbi_entrez",
        "pdbe",
        "alphafold",
        "chembl",
        "europe_pmc",
        "open_targets",
        "ensembl",
        "reactome",
    }
    registered_ids = {c.id for c in connectors}
    assert expected_ids == registered_ids


def test_registry_lookup_by_category() -> None:
    reg = DatabaseRegistry()
    structures = reg.list_by_category(DatabaseCategory.STRUCTURES)
    struct_ids = {c.db_id for c in structures}
    assert "rcsb_pdb" in struct_ids
    assert "pdbe" in struct_ids
    assert "alphafold" in struct_ids


@pytest.mark.asyncio
async def test_search_partial_failure_tolerance() -> None:
    """A failed database must not prevent results from other databases from appearing."""
    reg = DatabaseRegistry()
    reg._connectors.clear()
    reg.register(DummySuccessConnector())
    reg.register(DummyFailingConnector())

    req = GlobalSearchRequest(query="BRCA1", page=1, limit=5)
    resp = await reg.search_all(req)

    assert resp.total_results == 1
    assert "proteins" in resp.results_by_category
    assert resp.results_by_category["proteins"][0].id == "REC123"

    # Status array shows one OK and one failed
    status_map = {s["database_id"]: s["status"] for s in resp.database_statuses}
    assert status_map["dummy_success"] == "ok"
    assert status_map["dummy_fail"] == "failed"


@pytest.mark.asyncio
async def test_search_database_filter() -> None:
    reg = DatabaseRegistry()
    reg._connectors.clear()
    reg.register(DummySuccessConnector())
    reg.register(DummyFailingConnector())

    req = GlobalSearchRequest(query="BRCA1", databases=["dummy_success"])
    resp = await reg.search_all(req)

    assert resp.total_results == 1
    assert len(resp.database_statuses) == 1
    assert resp.database_statuses[0]["database_id"] == "dummy_success"


def test_api_list_connectors(client: TestClient) -> None:
    resp = client.get("/api/v1/databases/connectors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 11
    ids = [d["id"] for d in data]
    assert "rcsb_pdb" in ids
    assert "uniprot" in ids
    assert "chembl" in ids


def test_api_global_search(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.databases.registry.registry.search_all",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = {
            "query": "TP53",
            "total_results": 2,
            "execution_time_ms": 45.2,
            "categories_found": ["genes", "proteins"],
            "results_by_category": {
                "genes": [
                    {
                        "id": "7157",
                        "source_database": "ncbi_entrez",
                        "database_name": "NCBI Entrez",
                        "category": "genes",
                        "title": "TP53: tumor protein p53",
                        "external_url": "https://www.ncbi.nlm.nih.gov/gene/7157",
                        "metadata": {},
                    }
                ],
                "proteins": [
                    {
                        "id": "P04637",
                        "source_database": "uniprot",
                        "database_name": "UniProtKB",
                        "category": "proteins",
                        "title": "Cellular tumor antigen p53",
                        "external_url": "https://www.uniprot.org/uniprotkb/P04637",
                        "metadata": {},
                    }
                ],
            },
            "database_statuses": [
                {"database_id": "ncbi_entrez", "status": "ok", "hits": 1},
                {"database_id": "uniprot", "status": "ok", "hits": 1},
            ],
        }

        resp = client.post("/api/v1/databases/search", json={"query": "TP53", "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] == 2
        assert "genes" in data["results_by_category"]
        assert "proteins" in data["results_by_category"]


def test_api_get_record_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/databases/unknown_db/record/123")
    assert resp.status_code == 404
    assert "connector 'unknown_db' not found" in resp.json()["detail"].lower()

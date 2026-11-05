from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bioinformatics.genes.client import GeneClientError, GeneNotFoundError
from app.bioinformatics.genes.utils import (
    build_external_references,
    normalize_gene_query,
    normalize_species,
)
from app.models.gene_cache import GeneCache

MOCK_MYGENE_SEARCH = {
    "total": 1,
    "hits": [
        {
            "_id": "672",
            "symbol": "BRCA1",
            "name": "BRCA1 DNA repair associated",
            "taxid": 9606,
            "entrezgene": 672,
            "ensembl": {"gene": "ENSG00000012048"},
            "genomic_pos": {
                "chr": "17",
                "start": 43044295,
                "end": 43170245,
                "strand": -1,
                "ensemblgene": "ENSG00000012048",
            },
            "type_of_gene": "protein-coding",
            "alias": ["BRCAI", "BRCC1", "PPP1R53", "RNF53"],
            "_score": 24.5,
        }
    ],
}

MOCK_MYGENE_RECORD = {
    "_id": "672",
    "symbol": "BRCA1",
    "name": "BRCA1 DNA repair associated",
    "taxid": 9606,
    "entrezgene": 672,
    "ensembl": {"gene": "ENSG00000012048"},
    "genomic_pos": {
        "chr": "17",
        "start": 43044295,
        "end": 43170245,
        "strand": -1,
        "ensemblgene": "ENSG00000012048",
    },
    "type_of_gene": "protein-coding",
    "summary": "This gene encodes a nuclear phosphoprotein that plays a role in maintaining genomic stability.",
    "alias": ["BRCAI", "BRCC1", "RNF53"],
}


def test_search_genes_success(client: TestClient) -> None:
    """Verify gene search returns formatted results from biological API client."""
    with patch(
        "app.bioinformatics.genes.service.gene_service.client.search_mygene",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = MOCK_MYGENE_SEARCH

        response = client.get("/api/v1/genes/search?q=BRCA1&species=human&limit=5")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["query"] == "BRCA1"
        assert data["species"] == "human"
        assert data["total"] == 1
        assert len(data["results"]) == 1

        gene = data["results"][0]
        assert gene["symbol"] == "BRCA1"
        assert gene["entrez_id"] == "672"
        assert gene["ensembl_id"] == "ENSG00000012048"
        assert gene["chromosome"] == "17"
        assert gene["type_of_gene"] == "protein-coding"
        assert "BRCAI" in gene["aliases"]


def test_search_genes_validation(client: TestClient) -> None:
    """Ensure search endpoint rejects invalid query parameters."""
    # Missing required query param q
    res_missing = client.get("/api/v1/genes/search")
    assert res_missing.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Empty query param q
    res_empty = client.get("/api/v1/genes/search?q=")
    assert res_empty.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Limit greater than 50
    res_limit = client.get("/api/v1/genes/search?q=BRCA1&limit=999")
    assert res_limit.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_search_genes_upstream_error(client: TestClient) -> None:
    """Check that biological API errors are converted to 502 with structured message."""
    with patch(
        "app.bioinformatics.genes.service.gene_service.client.search_mygene",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.side_effect = GeneClientError("MyGene upstream gateway timeout", status_code=504)

        response = client.get("/api/v1/genes/search?q=TP53")
        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert "gateway timeout" in response.json()["detail"].lower()


def test_get_gene_detail_cold_fetch_and_cache(client: TestClient, db_session: Session) -> None:
    """Verify detail retrieval populates the database cache, and subsequent calls hit cache."""
    with patch(
        "app.bioinformatics.genes.service.gene_service.client.get_mygene_record",
        new_callable=AsyncMock,
    ) as mock_get_record:
        mock_get_record.return_value = MOCK_MYGENE_RECORD

        # 1. First call (cold fetch - not cached)
        response1 = client.get("/api/v1/genes/BRCA1")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        assert data1["symbol"] == "BRCA1"
        assert data1["id"] == "672"
        assert data1["cached"] is False
        assert data1["genomic_location"]["chromosome"] == "17"
        assert data1["genomic_location"]["start"] == 43044295
        assert len(data1["references"]) >= 3
        assert mock_get_record.call_count == 1

        # Verify entry exists in SQLite database
        cached_row = db_session.execute(
            select(GeneCache).where(GeneCache.symbol == "BRCA1")
        ).scalars().first()
        assert cached_row is not None
        assert cached_row.gene_id == "672"

        # 2. Second call should hit the database cache without calling external API
        response2 = client.get("/api/v1/genes/BRCA1")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["symbol"] == "BRCA1"
        assert data2["cached"] is True
        assert mock_get_record.call_count == 1  # No additional upstream call

        # 3. Third call with force_refresh=true should re-fetch from upstream
        response3 = client.get("/api/v1/genes/BRCA1?force_refresh=true")
        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()
        assert data3["cached"] is False
        assert mock_get_record.call_count == 2


def test_get_gene_detail_not_found(client: TestClient) -> None:
    """Verify unknown gene returns 404."""
    with patch(
        "app.bioinformatics.genes.service.gene_service.client.get_mygene_record",
        new_callable=AsyncMock,
    ) as mock_get_record:
        mock_get_record.side_effect = GeneNotFoundError("XYZ999NONEXISTENT")

        response = client.get("/api/v1/genes/XYZ999NONEXISTENT")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


def test_get_gene_references(client: TestClient) -> None:
    """Verify direct references endpoint returns validated cross-database URLs."""
    with patch(
        "app.bioinformatics.genes.service.gene_service.client.get_mygene_record",
        new_callable=AsyncMock,
    ) as mock_get_record:
        mock_get_record.return_value = MOCK_MYGENE_RECORD

        response = client.get("/api/v1/genes/672/references")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["gene_id"] == "672"
        assert data["symbol"] == "BRCA1"
        assert len(data["references"]) > 0

        db_names = [ref["database"] for ref in data["references"]]
        assert "NCBI Gene" in db_names
        assert "Ensembl" in db_names
        assert "HGNC" in db_names

        for ref in data["references"]:
            assert ref["url"].startswith("http")


def test_gene_utils_normalization_and_references() -> None:
    """Test utility normalization and URL generation functions."""
    assert normalize_gene_query("  tp53  ") == "tp53"
    assert normalize_species("Human") == "human"
    assert normalize_species("Homo sapiens") == "human"
    assert normalize_species("mus musculus") == "mouse"

    refs = build_external_references(
        symbol="TP53",
        entrez_id="7157",
        ensembl_id="ENSG00000141510",
        species="human",
        taxid=9606,
    )
    ref_dbs = {r.database: r.url for r in refs}
    assert "https://www.ncbi.nlm.nih.gov/gene/7157" in ref_dbs.values()
    assert "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000141510" in ref_dbs.values()
    assert "https://www.genecards.org/cgi-bin/carddisp.pl?gene=TP53" in ref_dbs.values()

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

MOCK_DISEASE_SEARCH_HITS = [
    {
        "id": "EFO_0000270",
        "name": "asthma",
        "description": "A chronic disease of the lungs and airways.",
        "entity": "disease",
    }
]

MOCK_DISEASE_DETAIL = {
    "id": "EFO_0000270",
    "name": "asthma",
    "description": "A chronic disease of the lungs and airways.",
    "synonyms": ["bronchial asthma", "hyperreactive airway disease"],
    "therapeuticAreas": [{"id": "EFO_0000684", "name": "respiratory system disease"}],
    "associatedTargets": {
        "count": 1,
        "rows": [
            {
                "score": 0.85,
                "target": {
                    "id": "ENSG00000012048",
                    "approvedSymbol": "BRCA1",
                    "approvedName": "BRCA1 DNA repair associated",
                },
            }
        ],
    },
}

MOCK_LITERATURE = [
    {
        "id": "12345678",
        "source": "MED",
        "pmid": "12345678",
        "doi": "10.1000/182",
        "title": "Genetic markers in asthma: A multicenter clinical study",
        "authorString": "Smith J, Doe A",
        "journalTitle": "Lancet Respir Med",
        "pubYear": "2024",
    }
]


def test_search_diseases(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.diseases.client.DiseaseClient.search_diseases",
        new_callable=AsyncMock,
        return_value=(1, MOCK_DISEASE_SEARCH_HITS),
    ):
        response = client.get("/api/v1/diseases/search?q=asthma")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == "EFO_0000270"
        assert data["results"][0]["name"] == "asthma"


def test_get_disease_details(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.diseases.client.DiseaseClient.get_disease_details",
        new_callable=AsyncMock,
        return_value=MOCK_DISEASE_DETAIL,
    ):
        response = client.get("/api/v1/diseases/EFO_0000270")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "EFO_0000270"
        assert data["name"] == "asthma"
        assert len(data["associated_targets"]) == 1
        assert data["associated_targets"][0]["symbol"] == "BRCA1"


def test_get_disease_literature(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.diseases.client.DiseaseClient.search_publications",
        new_callable=AsyncMock,
        return_value=(1, MOCK_LITERATURE),
    ):
        response = client.get("/api/v1/diseases/EFO_0000270/publications?name=asthma")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["publications"]) == 1
        assert data["publications"][0]["pmid"] == "12345678"
        assert "Smith J" in data["publications"][0]["authors"]

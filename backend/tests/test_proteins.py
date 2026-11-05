from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bioinformatics.proteins.client import ProteinClientError, ProteinNotFoundError
from app.bioinformatics.proteins.utils import (
    analyze_protein_sequence,
    build_protein_fasta,
    build_protein_references,
    is_valid_uniprot_accession,
    normalize_species_for_uniprot,
    validate_uniprot_accession,
)
from app.models.protein_cache import ProteinCache

MOCK_UNIPROT_SEARCH = {
    "total": 1,
    "results": [
        {
            "primaryAccession": "P68871",
            "uniProtkbId": "HBB_HUMAN",
            "entryType": "UniProtKB reviewed (Swiss-Prot)",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Hemoglobin subunit beta"}}
            },
            "genes": [{"geneName": {"value": "HBB"}}],
            "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
            "sequence": {"length": 147},
            "score": 100.0,
        }
    ],
}

MOCK_UNIPROT_RECORD = {
    "primaryAccession": "P68871",
    "uniProtkbId": "HBB_HUMAN",
    "entryType": "UniProtKB reviewed (Swiss-Prot)",
    "proteinDescription": {
        "recommendedName": {"fullName": {"value": "Hemoglobin subunit beta"}},
        "alternativeNames": [{"fullName": {"value": "Beta-globin"}}],
    },
    "genes": [{"geneName": {"value": "HBB"}}],
    "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
    "sequence": {
        "value": (
            "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFS"
            "DGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
        ),
        "length": 147,
        "molWeight": 15998,
    },
    "proteinExistence": "1: Evidence at protein level",
    "comments": [
        {
            "commentType": "FUNCTION",
            "texts": [
                {
                    "value": (
                        "Involved in oxygen transport from the lung to the various peripheral tissues."
                    )
                }
            ],
        },
        {
            "commentType": "SUBCELLULAR LOCATION",
            "subcellularLocations": [{"location": {"value": "Cytoplasm"}}],
        },
        {
            "commentType": "PTM",
            "texts": [{"value": "Acetylated at Ala-2; removes initial Met."}],
        },
    ],
    "features": [
        {
            "type": "Chain",
            "description": "Hemoglobin subunit beta",
            "location": {"start": {"value": 2}, "end": {"value": 147}},
        },
        {
            "type": "Modified residue",
            "description": "N-acetylalanine",
            "location": {"start": {"value": 2}, "end": {"value": 2}},
        },
    ],
    "uniProtKBCrossReferences": [
        {
            "database": "PDB",
            "id": "4HHB",
            "properties": [
                {"key": "Method", "value": "X-ray"},
                {"key": "Resolution", "value": "1.74 A"},
                {"key": "Chains", "value": "B/D=2-147"},
            ],
        },
        {
            "database": "AlphaFoldDB",
            "id": "P68871",
            "properties": [],
        },
        {
            "database": "RefSeq",
            "id": "NP_000509.1",
            "properties": [],
        },
    ],
}

MOCK_ALPHAFOLD_PREDICTION = {
    "entryId": "AF-P68871-F1",
    "gene": "HBB",
    "uniprotAccession": "P68871",
    "globalMetricValue": 97.19,
    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v6.pdb",
    "cifUrl": "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v6.cif",
}


def test_search_proteins_success(client: TestClient) -> None:
    """Verify protein search endpoint returns formatted results from UniProt client."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.search_uniprot",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = MOCK_UNIPROT_SEARCH

        response = client.get("/api/v1/proteins/search?q=hemoglobin&species=human&limit=5")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["query"] == "hemoglobin"
        assert data["species"] == "human"
        assert data["total"] == 1
        assert len(data["results"]) == 1

        hit = data["results"][0]
        assert hit["accession"] == "P68871"
        assert hit["entry_name"] == "HBB_HUMAN"
        assert hit["protein_name"] == "Hemoglobin subunit beta"
        assert hit["gene_name"] == "HBB"
        assert hit["organism"] == "Homo sapiens"
        assert hit["taxid"] == 9606
        assert hit["length"] == 147
        assert hit["reviewed"] is True


def test_search_proteins_validation(client: TestClient) -> None:
    """Verify parameter validation rejects empty query or excessive limits."""
    # Missing required query param q
    res_missing = client.get("/api/v1/proteins/search")
    assert res_missing.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Empty query param q
    res_empty = client.get("/api/v1/proteins/search?q=")
    assert res_empty.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Limit greater than 50
    res_limit = client.get("/api/v1/proteins/search?q=insulin&limit=999")
    assert res_limit.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_search_proteins_upstream_error(client: TestClient) -> None:
    """Ensure upstream service failures map to 502 with clean diagnostic message."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.search_uniprot",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.side_effect = ProteinClientError("UniProt gateway error", status_code=502)

        response = client.get("/api/v1/proteins/search?q=kinase")
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "gateway error" in response.json()["detail"].lower()


def test_get_protein_detail_cold_fetch_and_cache(client: TestClient, db_session: Session) -> None:
    """Verify detail retrieval populates SQLite test DB, and subsequent requests hit cache."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_uniprot_entry",
        new_callable=AsyncMock,
    ) as mock_get_entry:
        mock_get_entry.return_value = MOCK_UNIPROT_RECORD

        # 1. First call (cold fetch - uncached)
        response1 = client.get("/api/v1/proteins/P68871")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        assert data1["accession"] == "P68871"
        assert data1["entry_name"] == "HBB_HUMAN"
        assert data1["protein_name"] == "Hemoglobin subunit beta"
        assert data1["gene_name"] == "HBB"
        assert data1["sequence_length"] == 147
        assert "oxygen transport" in data1["function_summary"].lower()
        assert data1["subcellular_location"] == "Cytoplasm"
        assert data1["pdb_structures_count"] == 1
        assert data1["has_alphafold"] is True
        assert data1["cached"] is False
        assert mock_get_entry.call_count == 1

        # Verify record exists in SQLite test database
        cached_row = db_session.execute(
            select(ProteinCache).where(ProteinCache.accession == "P68871")
        ).scalars().first()
        assert cached_row is not None
        assert cached_row.accession == "P68871"
        assert cached_row.gene_name == "HBB"

        # 2. Second call should hit the database cache without contacting UniProt
        response2 = client.get("/api/v1/proteins/P68871")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["accession"] == "P68871"
        assert data2["cached"] is True
        assert mock_get_entry.call_count == 1

        # 3. Third call with force_refresh=true bypasses cache
        response3 = client.get("/api/v1/proteins/P68871?force_refresh=true")
        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()
        assert data3["cached"] is False
        assert mock_get_entry.call_count == 2


def test_get_protein_detail_invalid_accession(client: TestClient) -> None:
    """Ensure malformed UniProt accession returns 400 Bad Request."""
    response = client.get("/api/v1/proteins/invalid_accession_123")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid uniprot accession format" in response.json()["detail"].lower()


def test_get_protein_detail_not_found(client: TestClient) -> None:
    """Verify unknown accession returns 404 Not Found."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_uniprot_entry",
        new_callable=AsyncMock,
    ) as mock_get_entry:
        mock_get_entry.side_effect = ProteinNotFoundError("P99999")

        response = client.get("/api/v1/proteins/P99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


def test_get_protein_sequence_analysis(client: TestClient) -> None:
    """Verify genuine Biopython sequence properties calculation endpoint."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_uniprot_entry",
        new_callable=AsyncMock,
    ) as mock_get_entry:
        mock_get_entry.return_value = MOCK_UNIPROT_RECORD

        response = client.get("/api/v1/proteins/P68871/sequence")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["accession"] == "P68871"
        assert data["length"] == 147
        assert data["is_canonical_only"] is True
        assert data["fasta"].startswith(">sp|P68871|Hemoglobin subunit beta")

        props = data["properties"]
        assert props["theoretical_molecular_weight_da"] is not None
        assert 15000 < props["theoretical_molecular_weight_da"] < 17000
        assert props["isoelectric_point"] is not None
        assert 6.0 < props["isoelectric_point"] < 8.0
        assert props["aromaticity"] is not None
        assert props["instability_index"] is not None
        assert props["gravy_score"] is not None
        assert len(props["computational_notes"]) >= 3

        comp = data["composition"]
        assert comp["counts"]["V"] > 0
        assert comp["percentages"]["V"] > 0
        assert len(comp["non_canonical"]) == 0


def test_get_protein_structures_rcsb_and_alphafold(client: TestClient) -> None:
    """Verify 3D structures endpoint separates experimental PDB from AlphaFold AI predictions."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_uniprot_entry",
        new_callable=AsyncMock,
    ) as mock_get_entry, patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_alphafold_prediction",
        new_callable=AsyncMock,
    ) as mock_get_af:
        mock_get_entry.return_value = MOCK_UNIPROT_RECORD
        mock_get_af.return_value = MOCK_ALPHAFOLD_PREDICTION

        response = client.get("/api/v1/proteins/P68871/structures")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["accession"] == "P68871"
        assert data["experimental_count"] == 1
        assert data["predicted_available"] is True

        # Experimental structure verification
        exp = data["experimental_structures"][0]
        assert exp["pdb_id"] == "4HHB"
        assert exp["method"] == "X-ray"
        assert exp["resolution_angstrom"] == 1.74
        assert exp["is_experimental"] is True

        # AlphaFold prediction verification (must NOT be labeled experimental)
        pred = data["predicted_structure"]
        assert pred["entry_id"] == "AF-P68871-F1"
        assert pred["global_plddt"] == 97.19
        assert pred["confidence_category"] == "Very High (>90 pLDDT)"
        assert pred["is_experimental"] is False
        assert "not an experimentally determined structure" in pred["prediction_note"].lower()


def test_get_protein_references(client: TestClient) -> None:
    """Verify cross-database references endpoint returns validated biological URLs."""
    with patch(
        "app.bioinformatics.proteins.service.protein_service.client.get_uniprot_entry",
        new_callable=AsyncMock,
    ) as mock_get_entry:
        mock_get_entry.return_value = MOCK_UNIPROT_RECORD

        response = client.get("/api/v1/proteins/P68871/references")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["accession"] == "P68871"
        dbs = [r["database"] for r in data["references"]]
        assert "UniProtKB" in dbs
        assert "AlphaFold DB" in dbs
        assert "RCSB PDB" in dbs
        assert "GeneCards" in dbs

        for ref in data["references"]:
            assert ref["url"].startswith("http")


def test_protein_utils_validation_and_calculations() -> None:
    """Unit tests for protein utility functions."""
    assert validate_uniprot_accession("p68871") == "P68871"
    assert validate_uniprot_accession("P04637") == "P04637"
    assert is_valid_uniprot_accession("Q9BYF1") is True
    assert is_valid_uniprot_accession("invalid_acc") is False

    assert normalize_species_for_uniprot("Human") == 9606
    assert normalize_species_for_uniprot("Mus musculus") == 10090
    assert normalize_species_for_uniprot("all") is None

    # Test FASTA generation
    fasta = build_protein_fasta("P12345", "Test Protein", "Homo sapiens", "MVHLTPEEKS")
    assert fasta.startswith(">sp|P12345|Test Protein OS=Homo sapiens\nMVHLTPEEKS")

    # Test ambiguous sequence handling
    ambig_analysis = analyze_protein_sequence("P00000", "Ambiguous Protein", "MVHLTXEEKS")
    assert ambig_analysis.is_canonical_only is False
    assert "X" in ambig_analysis.composition.non_canonical
    assert ambig_analysis.properties.theoretical_molecular_weight_da is None
    assert any("ambiguous" in note.lower() for note in ambig_analysis.properties.computational_notes)

    # Test reference builder
    refs = build_protein_references("P68871", "HBB", "Homo sapiens", ["4HHB"])
    ref_dbs = {r.database: r.url for r in refs}
    assert "https://www.uniprot.org/uniprotkb/P68871" in ref_dbs.values()
    assert "https://www.rcsb.org/structure/4HHB" in ref_dbs.values()
    assert "https://alphafold.ebi.ac.uk/entry/P68871" in ref_dbs.values()


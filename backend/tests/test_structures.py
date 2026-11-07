from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

MOCK_RCSB_ENTRY = {
    "rcsb_id": "4HHB",
    "struct": {"title": "The crystal structure of human deoxyhaemoglobin at 1.74 A resolution"},
    "exptl": [{"method": "X-RAY DIFFRACTION"}],
    "rcsb_entry_info": {
        "resolution_combined": [1.74],
        "deposited_atom_count": 4779,
        "polymer_monomer_count_protein": 574,
    },
    "rcsb_accession_info": {"initial_release_date": "1984-07-17T00:00:00Z"},
    "rcsb_binding_affinity": [],
}

MOCK_PDB_FILE = """HEADER    OXYGEN STORAGE                          17-JUL-84   4HHB
TITLE     THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN AT 1.74 A RESOLUTION
ATOM      1  N   VAL A   1       6.204  16.869   4.854  1.00 49.05           N
ATOM      2  CA  VAL A   1       6.913  17.759   4.607  1.00 46.85           C
HETATM 4383 FE   HEM A 142       8.286  17.078   5.213  1.00 13.91          FE
TER
END
"""

MOCK_ALPHAFOLD_ENTRY = {
    "entryId": "AF-P68871-F1",
    "gene": "HBB",
    "uniprotAccession": "P68871",
    "uniprotDescription": "Hemoglobin subunit beta",
    "organismScientificName": "Homo sapiens",
    "globalMetricValue": 96.8,
    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v4.pdb",
    "cifUrl": "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v4.cif",
}


def test_get_structure_metadata(client: TestClient) -> None:
    with (
        patch(
            "app.bioinformatics.structures.client.StructureClient.get_rcsb_entry",
            new_callable=AsyncMock,
            return_value=MOCK_RCSB_ENTRY,
        ),
        patch(
            "app.bioinformatics.structures.client.StructureClient.get_rcsb_pdb_text",
            new_callable=AsyncMock,
            return_value=MOCK_PDB_FILE,
        ),
    ):
        response = client.get("/api/v1/structures/4HHB")
        assert response.status_code == 200
        data = response.json()
        assert data["structure_id"] == "4HHB"
        assert "deoxyhaemoglobin" in data["title"].lower()
        assert data["resolution"] == 1.74
        assert data["is_experimental"] is True
        assert len(data["bound_ligands"]) >= 1
        assert data["bound_ligands"][0]["chemical_id"] == "HEM"


def test_get_structure_pdb_text(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.structures.client.StructureClient.get_rcsb_pdb_text",
        new_callable=AsyncMock,
        return_value=MOCK_PDB_FILE,
    ):
        response = client.get("/api/v1/structures/4HHB/pdb")
        assert response.status_code == 200
        assert "chemical/x-pdb" in response.headers["content-type"]
        assert "4HHB" in response.text


def test_get_alphafold_metadata(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.structures.client.StructureClient.get_alphafold_prediction",
        new_callable=AsyncMock,
        return_value=MOCK_ALPHAFOLD_ENTRY,
    ):
        response = client.get("/api/v1/structures/alphafold/P68871")
        assert response.status_code == 200
        data = response.json()
        assert data["entry_id"] == "AF-P68871-F1"
        assert data["global_plddt"] == 96.8
        assert data["confidence_category"] == "Very High (>90)"
        assert data["is_experimental"] is False

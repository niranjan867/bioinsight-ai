from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

SAMPLE_PDB_FOR_DOCKING = """HEADER    OXYGEN STORAGE                          17-JUL-84   4HHB
TITLE     THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN AT 1.74 A RESOLUTION
ATOM      1  N   VAL A   1       6.204  16.869   4.854  1.00 49.05           N
ATOM      2  CA  VAL A   1       6.913  17.759   4.607  1.00 46.85           C
ATOM      3  C   VAL A   1       8.000  17.000   4.000  1.00 40.00           C
ATOM      4  O   VAL A   1       8.500  16.000   4.500  1.00 40.00           O
ATOM      5  N   LEU A   2       8.200  17.500   3.000  1.00 35.00           N
ATOM      6  CA  LEU A   2       9.000  17.000   2.000  1.00 35.00           C
HETATM 4383 FE   HEM A 142       8.286  17.078   5.213  1.00 13.91          FE
HETATM 4384 CHA  HEM A 142       8.800  17.500   5.500  1.00 15.00           C
HETATM 4385 CHB  HEM A 142       7.800  16.800   5.100  1.00 15.00           C
TER
END
"""


def test_get_pdb_ligands(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.structures.client.StructureClient.get_rcsb_pdb_text",
        new_callable=AsyncMock,
        return_value=SAMPLE_PDB_FOR_DOCKING,
    ):
        response = client.get("/api/v1/docking/ligands/4HHB")
        assert response.status_code == 200
        data = response.json()
        assert data["pdb_id"] == "4HHB"
        assert len(data["ligands"]) == 1
        assert data["ligands"][0]["chemical_id"] == "HEM"
        assert data["ligands"][0]["atom_count"] == 3


def test_analyze_docking_interaction(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.structures.client.StructureClient.get_rcsb_pdb_text",
        new_callable=AsyncMock,
        return_value=SAMPLE_PDB_FOR_DOCKING,
    ):
        response = client.post(
            "/api/v1/docking/analyze",
            json={
                "pdb_id": "4HHB",
                "ligand_id": "HEM",
                "max_distance": 4.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pdb_id"] == "4HHB"
        assert data["ligand_id"] == "HEM"
        assert data["total_contacts"] > 0
        assert data["estimated_affinity_kcal_mol"] < 0
        assert data["pocket"]["center_xyz"] is not None
        assert data["pocket"]["estimated_volume_a3"] > 0

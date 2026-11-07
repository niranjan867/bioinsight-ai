from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

MOCK_COMPOUND_PROPERTIES = {
    "CID": 2244,
    "Title": "Aspirin",
    "MolecularFormula": "C9H8O4",
    "MolecularWeight": 180.16,
    "CanonicalSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
    "IUPACName": "2-acetyloxybenzoic acid",
    "XLogP": 1.2,
    "TPSA": 63.6,
    "HBondDonorCount": 1,
    "HBondAcceptorCount": 4,
    "RotatableBondCount": 3,
    "ExactMass": 180.042259,
}

MOCK_SDF_TEXT = """2244
  -OEChem-11072412343D

 13 13  0     0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
M  END
$$$$
"""


def test_search_compounds(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.compounds.client.CompoundClient.search_by_name",
        new_callable=AsyncMock,
        return_value=[MOCK_COMPOUND_PROPERTIES],
    ):
        response = client.get("/api/v1/compounds/search?q=aspirin")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["cid"] == 2244
        assert data["results"][0]["name"] == "Aspirin"
        assert data["results"][0]["molecular_weight"] == 180.16


def test_get_compound_details_and_lipinski(client: TestClient) -> None:
    with (
        patch(
            "app.bioinformatics.compounds.client.CompoundClient.get_by_cid",
            new_callable=AsyncMock,
            return_value=MOCK_COMPOUND_PROPERTIES,
        ),
        patch(
            "app.bioinformatics.compounds.client.CompoundClient.get_synonyms",
            new_callable=AsyncMock,
            return_value=["Acetylsalicylic acid", "Ecotrin"],
        ),
        patch(
            "app.bioinformatics.compounds.client.CompoundClient.find_chembl_molecule_by_inchi_key",
            new_callable=AsyncMock,
            return_value="CHEMBL25",
        ),
        patch(
            "app.bioinformatics.compounds.client.CompoundClient.get_chembl_mechanisms",
            new_callable=AsyncMock,
            return_value=[
                {
                    "mechanism_of_action": "Cyclooxygenase-1 inhibitor",
                    "action_type": "INHIBITOR",
                    "target_chembl_id": "CHEMBL221",
                }
            ],
        ),
    ):
        response = client.get("/api/v1/compounds/2244")
        assert response.status_code == 200
        data = response.json()
        assert data["cid"] == 2244
        assert data["name"] == "Aspirin"
        assert data["chembl_id"] == "CHEMBL25"

        # Lipinski Rule of 5 checks
        lipinski = data["lipinski"]
        assert lipinski["is_druglike"] is True
        assert lipinski["violations_count"] == 0
        assert lipinski["molecular_weight_pass"] is True
        assert lipinski["logp_pass"] is True
        assert lipinski["h_bond_donors_pass"] is True
        assert lipinski["h_bond_acceptors_pass"] is True


def test_get_compound_sdf(client: TestClient) -> None:
    with patch(
        "app.bioinformatics.compounds.client.CompoundClient.get_3d_sdf",
        new_callable=AsyncMock,
        return_value=MOCK_SDF_TEXT,
    ):
        response = client.get("/api/v1/compounds/2244/sdf")
        assert response.status_code == 200
        assert "chemical/x-mdl-sdfile" in response.headers["content-type"]
        assert "2244" in response.text

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.bioinformatics.docking.engine import parse_vina_output_pdbqt
from app.bioinformatics.docking.interactions import analyze_pose_interactions
from app.bioinformatics.docking.pocket import (
    detect_pocket_from_ligand,
    detect_pocket_from_residues,
)
from app.bioinformatics.docking.preparation import prepare_ligand, prepare_receptor

SAMPLE_PDB = """ATOM      1  N   ASP A   1      27.251  24.414   2.114  1.00 11.29           N
ATOM      2  CA  ASP A   1      25.885  24.754   2.565  1.00 12.68           C
ATOM      3  C   ASP A   1      24.965  25.431   1.560  1.00 12.19           C
ATOM      4  O   ASP A   1      24.444  26.495   1.884  1.00 12.79           O
ATOM      5  CB  ASP A   1      25.962  25.568   3.856  1.00 13.92           C
ATOM      6  CG  ASP A   1      24.634  25.761   4.555  1.00 15.65           C
ATOM      7  OD1 ASP A   1      23.633  25.077   4.258  1.00 16.59           O
ATOM      8  OD2 ASP A   1      24.596  26.620   5.448  1.00 16.79           O
ATOM      9  N   GLY A   2      24.733  24.845   0.387  1.00 11.66           N
ATOM     10  CA  GLY A   2      23.834  25.378  -0.627  1.00 12.26           C
ATOM     11  C   GLY A   2      22.428  25.526  -0.088  1.00 12.87           C
ATOM     12  O   GLY A   2      21.579  24.646  -0.285  1.00 13.39           O
HETATM   13  O   HOH A 101      28.120  26.000   1.500  1.00 15.00           O
HETATM   14  C1  LIG A 201      24.000  25.000   2.000  1.00 20.00           C
HETATM   15  O1  LIG A 201      24.200  25.200   2.200  1.00 20.00           O
END
"""

SAMPLE_VINA_PDBQT = """MODEL 1
REMARK VINA RESULT:    -7.850      0.000      0.000
ROOT
ATOM      1  C   UNL     1      24.100  25.100   2.100  1.00  0.00    +0.145 C 
ATOM      2  O   UNL     1      23.800  24.800   1.800  1.00  0.00    -0.426 OA
ENDROOT
TORSDOF 0
ENDMDL
MODEL 2
REMARK VINA RESULT:    -6.420      2.341      3.120
ROOT
ATOM      1  C   UNL     1      25.200  26.300   3.500  1.00  0.00    +0.145 C 
ATOM      2  O   UNL     1      25.000  26.100   3.200  1.00  0.00    -0.426 OA
ENDROOT
TORSDOF 0
ENDMDL
"""





def test_prepare_receptor_cleans_and_formats_pdbqt() -> None:
    clean_pdb, pdbqt_text, meta = prepare_receptor(SAMPLE_PDB, remove_water=True)
    assert "HOH" not in clean_pdb
    assert "HOH" not in pdbqt_text
    assert meta["atom_count"] == 12  # 12 standard amino acid atoms
    assert meta["residue_count"] == 2
    assert "A" in meta["chains"]
    assert any("LIG" in lig["chemical_id"] for lig in meta["detected_ligands"])
    # Check PDBQT charge and atom type columns
    assert "+0.000" in pdbqt_text
    assert "OA" in pdbqt_text or "N " in pdbqt_text


def test_prepare_ligand_generates_3d_conformer_and_pdbqt() -> None:
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    pdbqt_str, sdf_text, meta = prepare_ligand(smiles, input_type="smiles")
    assert "ROOT" in pdbqt_str
    assert "ATOM" in pdbqt_str
    assert "$$$$" in sdf_text
    assert meta["formula"] == "C9H8O4"
    assert meta["molecular_weight"] == pytest.approx(180.16, abs=0.5)
    assert meta["num_rotatable_bonds"] >= 2
    assert meta["num_heavy_atoms"] == 13


def test_detect_pocket_from_bound_ligand() -> None:
    box = detect_pocket_from_ligand(SAMPLE_PDB, ligand_resname="LIG", padding=4.0)
    assert box is not None
    assert box.center_x == pytest.approx(24.1, abs=0.2)
    assert box.center_y == pytest.approx(25.1, abs=0.2)
    assert box.center_z == pytest.approx(2.1, abs=0.2)
    assert box.size_x >= 15.0


def test_detect_pocket_from_residues() -> None:
    box = detect_pocket_from_residues(SAMPLE_PDB, selected_residues=["ASP1", "GLY2"], padding=4.0)
    assert box is not None
    assert 20.0 <= box.center_x <= 30.0
    assert box.size_x >= 15.0


def test_parse_vina_output_pdbqt() -> None:
    poses = parse_vina_output_pdbqt(SAMPLE_VINA_PDBQT)
    assert len(poses) == 2
    assert poses[0]["mode_number"] == 1
    assert poses[0]["affinity_kcal_mol"] == -7.850
    assert poses[0]["rmsd_lower_bound"] == 0.0
    assert poses[1]["mode_number"] == 2
    assert poses[1]["affinity_kcal_mol"] == -6.420
    assert poses[1]["rmsd_lower_bound"] == 2.341
    assert "ATOM" in poses[0]["pdb_block"]


def test_analyze_pose_interactions_contacts() -> None:
    docked_pose_pdb = """ATOM      1  C   LIG A   1      24.000  25.000   2.000  1.00  0.00           C
ATOM      2  O   LIG A   1      24.200  25.200   2.200  1.00  0.00           O
END
"""
    interaction = analyze_pose_interactions(
        receptor_pdb=SAMPLE_PDB,
        docked_pose_pdb=docked_pose_pdb,
        mode_number=1,
        affinity_kcal_mol=-7.85,
    )
    assert interaction.mode_number == 1
    assert interaction.total_contacts > 0
    assert len(interaction.interacting_residues) > 0
    # At least one contact should be within 4.2 Å
    assert interaction.contacts[0].distance_angstroms <= 4.2
    assert interaction.contacts[0].interaction_type in {"hydrogen_bond", "van_der_waals", "hydrophobic", "salt_bridge"}


def test_api_prepare_receptor(client: TestClient) -> None:
    resp = client.post("/api/v1/docking/prepare/receptor", json={"pdb_text": SAMPLE_PDB})
    assert resp.status_code == 200
    data = resp.json()
    assert data["atom_count"] == 12
    assert "A" in data["chains"]
    assert "suggested_box" in data


def test_api_prepare_ligand(client: TestClient) -> None:
    resp = client.post("/api/v1/docking/prepare/ligand", json={"smiles": "CC(=O)Oc1ccccc1C(=O)O", "name": "Aspirin"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["formula"] == "C9H8O4"
    assert data["num_heavy_atoms"] == 13


def test_api_detect_pocket(client: TestClient) -> None:
    resp = client.post("/api/v1/docking/pocket", json={"pdb_text": SAMPLE_PDB, "ligand_resname": "LIG"})
    assert resp.status_code == 200
    data = resp.json()
    assert "center_x" in data
    assert "size_x" in data


def test_api_submit_and_list_docking_jobs(client: TestClient) -> None:
    with patch("app.bioinformatics.docking.service._executor.submit") as mock_submit:
        payload = {
            "name": "Benchmark Docking Run",
            "protein_source": "custom",
            "protein_id": "Receptor_ASP",
            "protein_pdb_text": SAMPLE_PDB,
            "ligand_source": "smiles",
            "ligand_id": "Aspirin",
            "ligand_input": "CC(=O)Oc1ccccc1C(=O)O",
            "binding_pocket": {
                "center_x": 24.0,
                "center_y": 25.0,
                "center_z": 2.0,
                "size_x": 18.0,
                "size_y": 18.0,
                "size_z": 18.0,
            },
            "docking_config": {
                "exhaustiveness": 4,
                "num_modes": 5,
            },
        }

        resp = client.post("/api/v1/docking/jobs", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert data["name"] == "Benchmark Docking Run"
        assert data["status"] == "QUEUED"
        assert "id" in data
        mock_submit.assert_called_once()

        job_id = data["id"]
        # List jobs
        list_resp = client.get("/api/v1/docking/jobs")
        assert list_resp.status_code == 200
        jobs = list_resp.json()
        assert any(j["id"] == job_id for j in jobs)

        # Get job detail
        detail_resp = client.get(f"/api/v1/docking/jobs/{job_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == job_id
        assert "scientific_disclaimer" in detail

        # Test PDF report download
        pdf_resp = client.get(f"/api/v1/docking/jobs/{job_id}/report?format=pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 100
        assert pdf_resp.content.startswith(b"%PDF")

        # Test DOCX report download
        docx_resp = client.get(f"/api/v1/docking/jobs/{job_id}/report?format=docx")
        assert docx_resp.status_code == 200
        assert "officedocument" in docx_resp.headers["content-type"]
        assert len(docx_resp.content) > 100

        # Test non-existent job report 404
        bad_resp = client.get("/api/v1/docking/jobs/nonexistent-id-999/report?format=pdf")
        assert bad_resp.status_code == 404

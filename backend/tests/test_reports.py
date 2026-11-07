from fastapi.testclient import TestClient


def _get_auth_header(client: TestClient, email: str = "reportuser@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Report Tester"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_generate_standalone_pdf(client: TestClient) -> None:
    payload = {
        "title": "BRCA1 Cross-Cohort Genomic Investigation",
        "author_name": "BioInsight AI Research",
        "summary": "Comprehensive investigation into BRCA1 tumor suppressor variants across clinical cohorts.",
        "sections": [
            {
                "title": "Gene Intelligence & Loci",
                "content": "BRCA1 is located on chromosome 17q21.31 and encodes 1,863 amino acids.",
                "table_data": [
                    ["Property", "Value"],
                    ["Symbol", "BRCA1"],
                    ["Chromosome", "17"],
                    ["Ensembl", "ENSG00000012048"],
                ],
            }
        ],
        "references": ["Smith et al. Nature 2024", "Open Targets Platform v24.09"],
    }

    response = client.post("/api/v1/reports/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # Verify PDF magic bytes '%PDF'
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 500


def test_generate_standalone_docx(client: TestClient) -> None:
    payload = {
        "title": "Oncology Pharmacology Dossier",
        "author_name": "Dr. Rosalind Franklin",
        "summary": "Evaluation of small-molecule tyrosine kinase inhibitors.",
        "sections": [
            {
                "title": "Compound Profiles",
                "content": "Imatinib exhibits nanomolar affinity against BCR-ABL.",
            }
        ],
        "references": ["ChEMBL Database v34"],
    }

    response = client.post("/api/v1/reports/docx", json=payload)
    assert response.status_code == 200
    assert "officedocument.wordprocessingml" in response.headers["content-type"]
    # Verify zip magic bytes PK for docx
    assert response.content.startswith(b"PK")
    assert len(response.content) > 500


def test_export_project_to_pdf_and_docx(client: TestClient) -> None:
    headers = _get_auth_header(client, "exporter@example.com")

    # Create project
    proj = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Sickle Cell Multi-Omics Research", "description": "HBB variant investigation"},
    ).json()
    proj_id = proj["id"]

    # Add item
    client.post(
        f"/api/v1/projects/{proj_id}/items",
        headers=headers,
        json={
            "item_type": "protein",
            "item_id": "P68871",
            "title": "Hemoglobin subunit beta",
            "description": "Adult hemoglobin subunit",
        },
    )

    # Export to PDF
    pdf_res = client.get(f"/api/v1/reports/project/{proj_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # Export to DOCX
    docx_res = client.get(f"/api/v1/reports/project/{proj_id}/docx", headers=headers)
    assert docx_res.status_code == 200
    assert "officedocument.wordprocessingml" in docx_res.headers["content-type"]
    assert docx_res.content.startswith(b"PK")

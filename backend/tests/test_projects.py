from fastapi.testclient import TestClient


def _get_auth_header(client: TestClient, email: str = "projuser@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Project User"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_projects(client: TestClient) -> None:
    headers = _get_auth_header(client, "alice@example.com")

    # Initially empty
    res = client.get("/api/v1/projects", headers=headers)
    assert res.status_code == 200
    assert res.json() == []

    # Create project
    create_res = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "BRCA1 Mutation Analysis",
            "description": "Cross-cohort variant study",
            "tags": ["oncology", "genomics"],
        },
    )
    assert create_res.status_code == 201
    proj_data = create_res.json()
    assert proj_data["name"] == "BRCA1 Mutation Analysis"
    assert proj_data["tags"] == ["oncology", "genomics"]
    assert proj_data["items_count"] == 0

    # List shows 1 project
    list_res = client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["name"] == "BRCA1 Mutation Analysis"


def test_project_items_and_activities(client: TestClient) -> None:
    headers = _get_auth_header(client, "bob@example.com")

    # Create project
    proj = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Hemoglobin Variants Investigation"},
    ).json()
    proj_id = proj["id"]

    # Add gene item
    item_res = client.post(
        f"/api/v1/projects/{proj_id}/items",
        headers=headers,
        json={
            "item_type": "gene",
            "item_id": "672",
            "title": "BRCA1 - Breast cancer type 1 susceptibility protein",
            "description": "DNA repair gene",
            "metadata_json": {"symbol": "BRCA1", "tax_id": 9606},
        },
    )
    assert item_res.status_code == 201
    item = item_res.json()
    assert item["item_type"] == "gene"
    assert item["item_id"] == "672"

    # Add protein item
    client.post(
        f"/api/v1/projects/{proj_id}/items",
        headers=headers,
        json={
            "item_type": "protein",
            "item_id": "P68871",
            "title": "Hemoglobin subunit beta",
        },
    )

    # Fetch project details
    detail_res = client.get(f"/api/v1/projects/{proj_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["items"]) == 2
    assert len(detail["activities"]) >= 2  # item_added activities logged

    # Delete first item
    del_res = client.delete(
        f"/api/v1/projects/{proj_id}/items/{item['id']}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # Verify item removed
    detail_after = client.get(f"/api/v1/projects/{proj_id}", headers=headers).json()
    assert len(detail_after["items"]) == 1


def test_project_user_isolation(client: TestClient) -> None:
    headers_user1 = _get_auth_header(client, "user1@example.com")
    headers_user2 = _get_auth_header(client, "user2@example.com")

    # User 1 creates project
    proj = client.post(
        "/api/v1/projects",
        headers=headers_user1,
        json={"name": "Confidential Research"},
    ).json()
    proj_id = proj["id"]

    # User 2 tries to access User 1's project -> 404
    forbidden_res = client.get(f"/api/v1/projects/{proj_id}", headers=headers_user2)
    assert forbidden_res.status_code == 404

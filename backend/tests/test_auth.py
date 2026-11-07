from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "researcher@example.com",
            "password": "Password123!",
            "full_name": "Dr. Rosalind Franklin",
            "institution": "King's College London",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient) -> None:
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "Password123!",
            "full_name": "First User",
        },
    )
    # Second registration with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "AnotherPassword123!",
            "full_name": "Second User",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_login_success_and_me(client: TestClient) -> None:
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "ValidPassword999!",
            "full_name": "Auth Tester",
        },
    )

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "ValidPassword999!"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    token = tokens["access_token"]

    # Access protected /me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "loginuser@example.com"
    assert user_info["full_name"] == "Auth Tester"


def test_login_invalid_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpwd@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Test User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpwd@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_update_profile(client: TestClient) -> None:
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "updateuser@example.com",
            "password": "Password123!",
            "full_name": "Initial Name",
        },
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "updateuser@example.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]

    patch_res = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name", "institution": "Harvard Medical School"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["full_name"] == "Updated Name"
    assert data["institution"] == "Harvard Medical School"

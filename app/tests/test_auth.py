from datetime import timedelta

from services import auth_service


def test_login_success_returns_token(client, test_agent):
    response = client.post("/auth/login", json={"username": "testagent", "password": "testpass123"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_wrong_password_rejected(client, test_agent):
    response = client.post("/auth/login", json={"username": "testagent", "password": "wrongpass"})

    assert response.status_code == 401


def test_login_unknown_user_rejected(client, test_agent):
    response = client.post("/auth/login", json={"username": "nosuchagent", "password": "testpass123"})

    assert response.status_code == 401


def test_token_contains_expected_claims(client, test_agent):
    response = client.post("/auth/login", json={"username": "testagent", "password": "testpass123"})
    token = response.json()["access_token"]

    payload = auth_service.decode_access_token(token)

    assert payload["sub"] == "testagent"
    assert payload["agent_id"] == test_agent.id
    assert payload["display_name"] == "Test Agent"


def test_protected_route_requires_token(client, test_agent):
    response = client.get("/settings/api-key")

    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client, auth_headers):
    response = client.get("/settings/api-key", headers=auth_headers)

    assert response.status_code == 200


def test_protected_route_rejects_invalid_token(client, test_agent):
    response = client.get("/settings/api-key", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_protected_route_rejects_expired_token(client, test_agent):
    expired_token = auth_service.create_access_token(test_agent, expires_delta=timedelta(minutes=-1))

    response = client.get("/settings/api-key", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401

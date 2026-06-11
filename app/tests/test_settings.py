import os

from services import settings_service


def test_api_key_not_configured_by_default(client):
    settings_service.clear_api_key()

    response = client.get("/settings/api-key")

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["masked_key"] is None


def test_set_api_key_masks_value_and_does_not_persist(client):
    response = client.put("/settings/api-key", json={"api_key": "sk-ant-api03-fake-key-1234"})

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    assert body["masked_key"].startswith("sk-ant")
    assert body["masked_key"].endswith("1234")
    assert "fake-key" not in body["masked_key"]
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-api03-fake-key-1234"

    settings_service.clear_api_key()


def test_delete_api_key_clears_env(client):
    settings_service.set_api_key("sk-ant-api03-fake-key-5678")

    response = client.delete("/settings/api-key")

    assert response.status_code == 200
    assert response.json() == {"configured": False, "masked_key": None, "connected": False, "message": None}
    assert "ANTHROPIC_API_KEY" not in os.environ

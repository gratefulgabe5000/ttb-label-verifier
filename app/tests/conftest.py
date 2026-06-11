import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("UPLOAD_DIR", "./data/test-uploads")

from main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client

    # The :memory: DB uses a single shared connection (StaticPool) that
    # outlives this test, so wipe tables to keep tests isolated.
    from db import Base, engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_agent(client):
    from db import SessionLocal
    from models.agent import Agent
    from services.auth_service import hash_password

    db = SessionLocal()
    try:
        agent = Agent(
            username="testagent",
            display_name="Test Agent",
            password_hash=hash_password("testpass123"),
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
    finally:
        db.close()

    return agent


@pytest.fixture()
def auth_headers(client, test_agent):
    response = client.post("/auth/login", json={"username": "testagent", "password": "testpass123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

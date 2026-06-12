"""Batch Orchestrator tests (WBS 9.3-9.5, A-07, IA-17, FR-074-077)."""

import asyncio
from pathlib import Path

import pytest

from services import batch_service, pipeline
from services.form_extraction import LOCATION_HINTS, PART_I_FIELDS, FieldResult

FIXTURES = Path(__file__).resolve().parent.parent.parent / "testdata"
SAMPLE_PDF = FIXTURES / "forms" / "sample_creek_acroform.pdf"


def _empty_form_results() -> dict[str, FieldResult]:
    return {field: FieldResult(None, None, None, None, LOCATION_HINTS.get(field)) for field in PART_I_FIELDS}


@pytest.fixture()
def db_session():
    import models  # noqa: F401  registers tables on Base.metadata
    from db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _upload(client, auth_headers) -> int:
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[("form_file", ("form.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
    )
    assert response.status_code == 201
    return response.json()["id"]


# ---------------------------------------------------------------------------
# 9.3 -- Batch Orchestrator concurrency bound (A-07/IA-17)
# ---------------------------------------------------------------------------


def test_run_batch_bounds_concurrent_extraction(db_session, monkeypatch):
    from models.application import Application

    applications = []
    for _ in range(5):
        application = Application(form_path="dummy.pdf", status="PENDING")
        db_session.add(application)
        applications.append(application)
    db_session.commit()
    for application in applications:
        db_session.refresh(application)

    batch = batch_service.create_batch(
        db_session, application_ids=[a.id for a in applications], created_by=None
    )

    in_flight = 0
    max_in_flight = 0

    async def fake_run_extraction(application, label_images, *, client=None):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.05)
        in_flight -= 1
        return _empty_form_results(), {}

    monkeypatch.setattr(pipeline, "run_extraction", fake_run_extraction)

    asyncio.run(batch_service.run_batch(db_session, batch, applications, concurrency=2))

    assert max_in_flight == 2

    for application in applications:
        db_session.refresh(application)
        assert application.status == "DETERMINED"

    db_session.refresh(batch)
    assert batch.completed_at is not None
    assert batch.approved_count + batch.denied_count + batch.exemption_count == 5


# ---------------------------------------------------------------------------
# 9.4/9.5 -- POST /batch/process, GET /batch/{id}/status (FR-074-077)
# ---------------------------------------------------------------------------


def test_process_batch_reaches_complete_with_summary_counts(client, auth_headers):
    application_ids = [_upload(client, auth_headers) for _ in range(3)]

    response = client.post("/batch/process", headers=auth_headers, json={"application_ids": application_ids})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETE"
    assert body["total"] == 3
    assert body["completed"] == 3
    assert body["completed_at"] is not None
    assert body["approved_count"] + body["denied_count"] + body["exemption_count"] == 3
    assert {a["id"] for a in body["applications"]} == set(application_ids)
    assert all(a["status"] == "DETERMINED" for a in body["applications"])
    assert all(a["recommendation"] is not None for a in body["applications"])


def test_get_batch_status_returns_same_summary(client, auth_headers):
    application_ids = [_upload(client, auth_headers) for _ in range(2)]
    process_response = client.post(
        "/batch/process", headers=auth_headers, json={"application_ids": application_ids}
    )
    batch_id = process_response.json()["id"]

    response = client.get(f"/batch/{batch_id}/status", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == batch_id
    assert body["status"] == "COMPLETE"
    assert body["total"] == 2
    assert body["completed"] == 2
    assert body["approved_count"] == process_response.json()["approved_count"]
    assert body["denied_count"] == process_response.json()["denied_count"]
    assert body["exemption_count"] == process_response.json()["exemption_count"]


def test_process_batch_404_for_unowned_application(client, auth_headers, second_auth_headers):
    application_id = _upload(client, auth_headers)

    response = client.post(
        "/batch/process", headers=second_auth_headers, json={"application_ids": [application_id]}
    )

    assert response.status_code == 404


def test_batch_status_404_for_other_agents_batch(client, auth_headers, second_auth_headers):
    application_ids = [_upload(client, auth_headers)]
    process_response = client.post(
        "/batch/process", headers=auth_headers, json={"application_ids": application_ids}
    )
    batch_id = process_response.json()["id"]

    response = client.get(f"/batch/{batch_id}/status", headers=second_auth_headers)

    assert response.status_code == 404


def test_batch_status_404_for_unknown_batch(client, auth_headers):
    response = client.get("/batch/999999/status", headers=auth_headers)

    assert response.status_code == 404

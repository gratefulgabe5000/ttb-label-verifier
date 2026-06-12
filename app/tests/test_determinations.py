"""Agent override & finalization tests (WBS 10.1/10.2/10.4, FR-086-090, SR-004, A-15)."""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent.parent / "testdata"
SAMPLE_PDF = FIXTURES / "forms" / "sample_creek_acroform.pdf"
SAMPLE_JPEG = FIXTURES / "synthetic" / "stollwolfe_for_sale_pa.jpg"


def _process_application(client, auth_headers) -> dict:
    upload_response = client.post(
        "/applications/upload",
        headers=auth_headers,
        data={"label_types": ["brand"]},
        files=[
            ("form_file", ("form.pdf", SAMPLE_PDF.read_bytes(), "application/pdf")),
            ("label_images", ("brand.jpg", SAMPLE_JPEG.read_bytes(), "image/jpeg")),
        ],
    )
    application_id = upload_response.json()["id"]

    process_response = client.post(f"/applications/{application_id}/process", headers=auth_headers)
    return process_response.json()


def test_override_parameter_records_audit_trail(client, auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]

    comparisons = client.get(f"/applications/{application['id']}/comparisons", headers=auth_headers).json()
    field_name = comparisons[0]["field_name"]
    original_result = comparisons[0]["result"]

    response = client.post(
        f"/determinations/{determination_id}/override",
        headers=auth_headers,
        json={"field": field_name, "override_value": "MATCH", "reason": "Verified manually against the label."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["application_id"] == application["id"]
    assert body["field"] == field_name
    assert body["original_value"] == original_result
    assert body["override_value"] == "MATCH"
    assert body["override_by"]
    assert body["override_reason"] == "Verified manually against the label."
    assert body["override_at"] is not None

    updated = client.get(f"/applications/{application['id']}/comparisons", headers=auth_headers).json()
    updated_comparison = next(c for c in updated if c["field_name"] == field_name)
    assert updated_comparison["result"] == original_result  # original AI determination retained (FR-088)
    assert updated_comparison["agent_override"] == "MATCH"
    assert updated_comparison["override_reason"] == "Verified manually against the label."


def test_override_overall_determination(client, auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]
    original_recommendation = application["determination"]["recommendation"]

    response = client.post(
        f"/determinations/{determination_id}/override",
        headers=auth_headers,
        json={"override_value": "APPROVE", "reason": "Manual review overrides the AI recommendation."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["field"] is None
    assert body["original_value"] == original_recommendation
    assert body["override_value"] == "APPROVE"

    detail = client.get(f"/applications/{application['id']}", headers=auth_headers).json()
    assert detail["determination"]["agent_override"] == "APPROVE"
    assert detail["determination"]["recommendation"] == original_recommendation  # AI output retained
    assert detail["determination"]["override_reason"] == "Manual review overrides the AI recommendation."


def test_override_rejects_blank_reason(client, auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]

    response = client.post(
        f"/determinations/{determination_id}/override",
        headers=auth_headers,
        json={"override_value": "APPROVE", "reason": "   "},
    )

    assert response.status_code == 422


def test_override_404_for_unknown_field(client, auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]

    response = client.post(
        f"/determinations/{determination_id}/override",
        headers=auth_headers,
        json={"field": "not_a_real_field", "override_value": "MATCH", "reason": "test"},
    )

    assert response.status_code == 404


def test_override_404_for_other_agents_determination(client, auth_headers, second_auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]

    response = client.post(
        f"/determinations/{determination_id}/override",
        headers=second_auth_headers,
        json={"override_value": "APPROVE", "reason": "test"},
    )

    assert response.status_code == 404


def test_finalize_sets_finalized_at(client, auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]
    assert application["determination"]["finalized_at"] is None

    response = client.post(f"/determinations/{determination_id}/finalize", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["finalized_at"] is not None


def test_finalize_404_for_other_agents_determination(client, auth_headers, second_auth_headers):
    application = _process_application(client, auth_headers)
    determination_id = application["determination"]["id"]

    response = client.post(f"/determinations/{determination_id}/finalize", headers=second_auth_headers)

    assert response.status_code == 404


def test_finalize_404_for_unknown_determination(client, auth_headers):
    response = client.post("/determinations/999999/finalize", headers=auth_headers)

    assert response.status_code == 404

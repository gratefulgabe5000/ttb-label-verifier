"""Stage 3-6 pipeline orchestration tests (WBS 9.1/9.2/9.6, FR-074, PR-001)."""

import time
from pathlib import Path

import pytest

from services.form_extraction import PART_I_FIELDS
from services.label_extraction import SIMPLE_FIELDS

FIXTURES = Path(__file__).resolve().parent.parent.parent / "testdata"
SAMPLE_PDF = FIXTURES / "forms" / "sample_creek_acroform.pdf"
SAMPLE_JPEG = FIXTURES / "synthetic" / "stollwolfe_for_sale_pa.jpg"


def _upload(client, auth_headers) -> dict:
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        data={"label_types": ["brand"]},
        files=[
            ("form_file", ("form.pdf", SAMPLE_PDF.read_bytes(), "application/pdf")),
            ("label_images", ("brand.jpg", SAMPLE_JPEG.read_bytes(), "image/jpeg")),
        ],
    )
    assert response.status_code == 201
    return response.json()


def test_process_runs_all_stages_and_reaches_determined(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]
    label_image_id = application["label_images"][0]["id"]

    response = client.post(f"/applications/{application_id}/process", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DETERMINED"
    assert body["processed_at"] is not None

    form_parameters = {p["field_name"]: p for p in body["form_parameters"]}
    assert len(form_parameters) == len(PART_I_FIELDS)
    assert form_parameters["brand_name"]["field_value"] == "Sample Creek"
    assert form_parameters["brand_name"]["extraction_method"] == "acroform"

    label_parameters = body["label_parameters"]
    assert len(label_parameters) == len(SIMPLE_FIELDS) + 1  # + government_warning
    assert all(p["label_image_id"] == label_image_id for p in label_parameters)

    determination = body["determination"]
    assert determination is not None
    assert determination["recommendation"] in ("APPROVE", "DENY", "RECOMMEND_EXEMPTION_REVIEW")


def test_process_persists_comparisons_retrievable_via_endpoint(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    process_response = client.post(f"/applications/{application_id}/process", headers=auth_headers)
    assert process_response.status_code == 200

    response = client.get(f"/applications/{application_id}/comparisons", headers=auth_headers)

    assert response.status_code == 200
    comparisons = response.json()
    assert len(comparisons) > 0
    assert all("field_name" in c and "result" in c for c in comparisons)


def test_process_404_for_other_agents_application(client, auth_headers, second_auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    response = client.post(f"/applications/{application_id}/process", headers=second_auth_headers)

    assert response.status_code == 404


def test_comparisons_empty_before_processing(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    response = client.get(f"/applications/{application_id}/comparisons", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_comparisons_404_for_other_agents_application(client, auth_headers, second_auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    response = client.get(f"/applications/{application_id}/comparisons", headers=second_auth_headers)

    assert response.status_code == 404


def test_single_application_processing_completes_within_pr001_budget(client, auth_headers):
    """PR-001: one application (1 form + label images) processed within 5 seconds."""
    application = _upload(client, auth_headers)
    application_id = application["id"]

    start = time.monotonic()
    response = client.post(f"/applications/{application_id}/process", headers=auth_headers)
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 5.0


# ---------------------------------------------------------------------------
# Per-stage reprocessing (Detail View "Reprocess" actions)
# ---------------------------------------------------------------------------


def test_reprocess_form_only_runs_stage3_and_refreshes_determination(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    assert client.post(f"/applications/{application_id}/process", headers=auth_headers).status_code == 200

    response = client.post(f"/applications/{application_id}/reprocess/form", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DETERMINED"

    form_parameters = {p["field_name"]: p for p in body["form_parameters"]}
    assert len(form_parameters) == len(PART_I_FIELDS)
    assert form_parameters["brand_name"]["field_value"] == "Sample Creek"

    # Stage 4 results are untouched by a form-only reprocess.
    assert len(body["label_parameters"]) == len(SIMPLE_FIELDS) + 1
    assert body["determination"] is not None


def test_reprocess_label_only_runs_stage4_and_refreshes_determination(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    assert client.post(f"/applications/{application_id}/process", headers=auth_headers).status_code == 200

    response = client.post(f"/applications/{application_id}/reprocess/label", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DETERMINED"

    assert len(body["label_parameters"]) == len(SIMPLE_FIELDS) + 1

    # Stage 3 results are untouched by a label-only reprocess.
    form_parameters = {p["field_name"]: p for p in body["form_parameters"]}
    assert len(form_parameters) == len(PART_I_FIELDS)
    assert body["determination"] is not None


def test_reprocess_comparison_only_recomputes_without_reextraction(client, auth_headers):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    processed = client.post(f"/applications/{application_id}/process", headers=auth_headers).json()

    response = client.post(f"/applications/{application_id}/reprocess/comparison", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DETERMINED"
    assert body["determination"] is not None

    # Stage 3/4 results are untouched by a comparison-only reprocess.
    assert body["form_parameters"] == processed["form_parameters"]
    assert body["label_parameters"] == processed["label_parameters"]

    comparisons = client.get(f"/applications/{application_id}/comparisons", headers=auth_headers).json()
    assert len(comparisons) > 0


@pytest.mark.parametrize("stage", ["form", "label", "comparison"])
def test_reprocess_404_for_other_agents_application(client, auth_headers, second_auth_headers, stage):
    application = _upload(client, auth_headers)
    application_id = application["id"]

    response = client.post(f"/applications/{application_id}/reprocess/{stage}", headers=second_auth_headers)

    assert response.status_code == 404

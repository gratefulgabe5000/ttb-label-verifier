from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent.parent / "testdata"
SAMPLE_PDF = FIXTURES / "forms" / "sample_creek_acroform.pdf"
SAMPLE_JPEG = FIXTURES / "synthetic" / "stollwolfe_for_sale_pa.jpg"

# Minimal valid signatures for FR-002 format coverage (no image library required).
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WEBP_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 32


def _pdf_bytes() -> bytes:
    return SAMPLE_PDF.read_bytes()


def _jpeg_bytes() -> bytes:
    return SAMPLE_JPEG.read_bytes()


def test_upload_creates_application_with_label_images(client, auth_headers):
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        data={
            "serial_number": "25304001000123",
            "applicant_name": "Stoll & Wolfe Distillery",
            "label_types": ["front"],
        },
        files=[
            ("form_file", ("form.pdf", _pdf_bytes(), "application/pdf")),
            ("label_images", ("front.jpg", _jpeg_bytes(), "image/jpeg")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["status"] == "PENDING"
    assert body["serial_number"] == "25304001000123"
    assert body["applicant_name"] == "Stoll & Wolfe Distillery"
    assert len(body["label_images"]) == 1
    assert body["label_images"][0]["label_type"] == "front"
    assert body["form_parameters"] == []
    assert body["label_parameters"] == []
    assert body["determination"] is None


def test_upload_rejects_non_pdf_form(client, auth_headers):
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[("form_file", ("form.docx", b"not a pdf", "application/octet-stream"))],
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_accepts_jpeg_png_and_webp_label_images(client, auth_headers):
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[
            ("form_file", ("form.pdf", _pdf_bytes(), "application/pdf")),
            ("label_images", ("front.jpg", _jpeg_bytes(), "image/jpeg")),
            ("label_images", ("back.png", PNG_BYTES, "image/png")),
            ("label_images", ("neck.webp", WEBP_BYTES, "image/webp")),
        ],
    )

    assert response.status_code == 201
    assert len(response.json()["label_images"]) == 3


def test_upload_rejects_invalid_label_image_format(client, auth_headers):
    response = client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[
            ("form_file", ("form.pdf", _pdf_bytes(), "application/pdf")),
            ("label_images", ("label.docx", b"not an image", "application/octet-stream")),
        ],
    )

    assert response.status_code == 400
    assert "label.docx" in response.json()["detail"]


def test_batch_upload_creates_separate_applications(client, auth_headers):
    ids = set()
    for _ in range(5):
        response = client.post(
            "/applications/upload",
            headers=auth_headers,
            files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
        )
        assert response.status_code == 201
        ids.add(response.json()["id"])

    assert len(ids) == 5

    list_response = client.get("/applications", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 5


def test_list_applications_filters_by_applicant_name(client, auth_headers):
    client.post(
        "/applications/upload",
        headers=auth_headers,
        data={"applicant_name": "Stoll & Wolfe Distillery"},
        files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
    )
    client.post(
        "/applications/upload",
        headers=auth_headers,
        data={"applicant_name": "Acme Beverage Co"},
        files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
    )

    response = client.get("/applications?applicant_name=Stoll", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["applicant_name"] == "Stoll & Wolfe Distillery"


def test_list_applications_excludes_other_agents(client, auth_headers, second_auth_headers):
    client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
    )
    client.post(
        "/applications/upload",
        headers=second_auth_headers,
        files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
    )

    response = client.get("/applications", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_application_returns_full_detail(client, auth_headers):
    upload_response = client.post(
        "/applications/upload",
        headers=auth_headers,
        data={"label_types": ["brand"]},
        files=[
            ("form_file", ("form.pdf", _pdf_bytes(), "application/pdf")),
            ("label_images", ("brand.jpg", _jpeg_bytes(), "image/jpeg")),
        ],
    )
    application_id = upload_response.json()["id"]

    response = client.get(f"/applications/{application_id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == application_id
    assert len(body["label_images"]) == 1
    assert body["label_images"][0]["label_type"] == "brand"
    assert body["determination"] is None


def test_get_application_404_for_other_agents_application(client, auth_headers, second_auth_headers):
    upload_response = client.post(
        "/applications/upload",
        headers=auth_headers,
        files=[("form_file", ("form.pdf", _pdf_bytes(), "application/pdf"))],
    )
    application_id = upload_response.json()["id"]

    response = client.get(f"/applications/{application_id}", headers=second_auth_headers)

    assert response.status_code == 404


def test_validate_form_file_enforces_20mb_limit():
    from services.application_service import FileValidationError, validate_form_file

    twenty_mb = b"%PDF" + b"\x00" * (20 * 1024 * 1024 - 4)
    validate_form_file("form.pdf", twenty_mb)  # exactly 20 MB — accepted

    with pytest.raises(FileValidationError):
        validate_form_file("form.pdf", twenty_mb + b"\x00")  # 20 MB + 1 byte — rejected


def test_validate_label_image_enforces_10mb_limit():
    from services.application_service import FileValidationError, validate_label_image

    ten_mb = b"\xff\xd8\xff" + b"\x00" * (10 * 1024 * 1024 - 3)
    validate_label_image("label.jpg", ten_mb)  # exactly 10 MB — accepted

    with pytest.raises(FileValidationError):
        validate_label_image("label.jpg", ten_mb + b"\x00")  # 10 MB + 1 byte — rejected

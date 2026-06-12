"""Stage 3 (Form Assessment, TS-01) tiered extraction tests (WBS 5.7)."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.form_extraction import (
    LOCATION_HINTS,
    PART_I_FIELDS,
    _split_name_address,
    extract_tier1,
    extract_tier2,
    extract_tier3,
    normalize_grape_varietals,
    normalize_product_type,
    normalize_serial_number,
    normalize_source,
    persist_form_parameters,
    run_stage3_extraction,
)

FORMS = Path(__file__).resolve().parent.parent.parent / "testdata" / "forms"
ACROFORM_PDF = FORMS / "sample_creek_acroform.pdf"
FLATTENED_PDF = FORMS / "sample_creek_flattened.pdf"
SCANNED_PDF = FORMS / "sample_creek_scanned.pdf"


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


def _mock_client(payload: dict) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.text = json.dumps(payload)
    response = MagicMock()
    response.content = [message]
    client.messages.create.return_value = response
    return client


# ---------------------------------------------------------------------------
# 5.4 — Normalization
# ---------------------------------------------------------------------------


class TestNormalization:
    def test_normalize_source(self):
        assert normalize_source("/Domes") == "domestic"
        assert normalize_source("/Import") == "imported"
        assert normalize_source("/Off") is None
        assert normalize_source(None) is None

    def test_normalize_product_type(self):
        assert normalize_product_type("/Wine") == "wine"
        assert normalize_product_type("/Spirits") == "distilled_spirits"
        assert normalize_product_type("/Malt") == "malt_beverages"
        assert normalize_product_type("/Off") is None

    def test_normalize_serial_number(self):
        assert normalize_serial_number("260001") == "26-1"
        assert normalize_serial_number("250304") == "25-304"
        assert normalize_serial_number("12") == "12"  # too few digits to parse
        assert normalize_serial_number(None) is None

    def test_normalize_grape_varietals(self):
        assert normalize_grape_varietals("Cabernet Sauvignon, Merlot") == ["Cabernet Sauvignon", "Merlot"]
        assert normalize_grape_varietals("Pinot Noir; Syrah\nGrenache") == ["Pinot Noir", "Syrah", "Grenache"]
        assert normalize_grape_varietals(None) is None
        assert normalize_grape_varietals("") is None

    def test_split_name_address(self):
        name, address = _split_name_address(
            "Sample Creek Distillery, LLC\n123 Distillery Lane\nWarner Robins, GA 31088"
        )
        assert name == "Sample Creek Distillery, LLC"
        assert address == "123 Distillery Lane\nWarner Robins, GA 31088"

        name, address = _split_name_address("Solo Name Only")
        assert name == "Solo Name Only"
        assert address is None

        assert _split_name_address(None) == (None, None)


# ---------------------------------------------------------------------------
# 5.1 — Tier 1 (pypdf AcroForm)
# ---------------------------------------------------------------------------


class TestTier1:
    def test_extracts_acroform_fields(self):
        results = extract_tier1(ACROFORM_PDF)

        assert results["brand_name"].value == "Sample Creek"
        assert results["brand_name"].extraction_method == "acroform"
        assert results["brand_name"].confidence == 1.0
        assert results["brand_name"].bbox == {"page": 0, "x": 21.9, "y": 213.4, "w": 224.2, "h": 15.7}

        assert results["fanciful_name"].value == "Heritage Reserve"
        assert results["plant_registry_number"].value == "DSP-GA-20123"
        assert results["phone_number"].value == "(478) 555-0142"
        assert results["email_address"].value == "compliance@samplecreekdistillery.com"
        assert results["date_of_application"].value == "06/01/2026"
        assert results["applicant_printed_name"].value == "Jordan T. Avery"

    def test_splits_applicant_name_and_address(self):
        results = extract_tier1(ACROFORM_PDF)
        assert results["applicant_name"].value == "Sample Creek Distillery, LLC"
        assert results["applicant_address"].value == "123 Distillery Lane\nWarner Robins, GA 31088"

    def test_normalizes_checkbox_fields(self):
        results = extract_tier1(ACROFORM_PDF)
        assert results["source"].value == "domestic"
        assert results["product_type"].value == "distilled_spirits"

    def test_normalizes_serial_number(self):
        results = extract_tier1(ACROFORM_PDF)
        assert results["serial_number"].value == "26-1"

    def test_application_type_checkbox_group(self):
        results = extract_tier1(ACROFORM_PDF)
        app_type = results["application_type"].value
        assert app_type["checked"] == ["14a"]
        assert app_type["exemption_state"] is None
        assert app_type["container_capacity"] is None
        assert app_type["prior_ttb_id"] is None

    def test_empty_fields_not_resolved(self):
        results = extract_tier1(ACROFORM_PDF)
        for field in ("representative_id", "mailing_address", "formula_id", "grape_varietals", "wine_appellation"):
            assert field not in results

    def test_no_acroform_returns_empty(self):
        assert extract_tier1(FLATTENED_PDF) == {}
        assert extract_tier1(SCANNED_PDF) == {}


# ---------------------------------------------------------------------------
# 5.2 — Tier 2 (pdfplumber text layer)
# ---------------------------------------------------------------------------


class TestTier2:
    def test_extracts_text_layer_values(self):
        results = extract_tier2(FLATTENED_PDF)

        assert results["plant_registry_number"].value == "DSP-GA-20123"
        assert results["brand_name"].value == "Sample Creek"
        assert results["fanciful_name"].value == "Heritage Reserve"
        assert results["phone_number"].value == "(478) 555-0142"
        assert results["email_address"].value == "compliance@samplecreekdistillery.com"
        assert results["embossed_info"].value == "NET CONTENTS 750 ML BLOWN INTO BASE OF BOTTLE"
        assert results["date_of_application"].value == "06/01/2026"
        assert results["applicant_printed_name"].value == "Jordan T. Avery"

        for fr in results.values():
            assert fr.extraction_method == "pdftext"
            assert fr.confidence == pytest.approx(0.92)

    def test_resolves_overlapping_item8_via_font_size(self):
        results = extract_tier2(FLATTENED_PDF)
        assert results["applicant_name"].value == "Sample Creek Distillery, LLC"
        assert results["applicant_address"].value == "123 Distillery Lane\nWarner Robins, GA 31088"

    def test_serial_number_digit_filter(self):
        results = extract_tier2(FLATTENED_PDF)
        assert results["serial_number"].value == "26-1"

    def test_empty_fields_filtered_by_label_match(self):
        results = extract_tier2(FLATTENED_PDF)
        for field in ("representative_id", "mailing_address", "formula_id", "grape_varietals", "wine_appellation"):
            assert field not in results

    def test_never_attempts_checkbox_or_signature_fields(self):
        results = extract_tier2(FLATTENED_PDF)
        for field in ("source", "product_type", "application_type", "signature_present", "foreign_translations"):
            assert field not in results

    def test_no_text_layer_returns_empty(self):
        assert extract_tier2(SCANNED_PDF) == {}


# ---------------------------------------------------------------------------
# 5.3 — Tier 3 (Claude Vision, mocked)
# ---------------------------------------------------------------------------


class TestTier3:
    def test_no_api_key_returns_empty(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert extract_tier3(SCANNED_PDF, ["brand_name"], client=None) == {}

    def test_no_needed_fields_returns_empty(self):
        client = _mock_client({"values": {}, "confidence_scores": {}})
        assert extract_tier3(SCANNED_PDF, [], client=client) == {}
        client.messages.create.assert_not_called()

    def test_extracts_vision_fields(self):
        client = _mock_client(
            {
                "values": {
                    "brand_name": "Sample Creek",
                    "signature_present": True,
                    "foreign_translations": None,
                },
                "confidence_scores": {"brand_name": 0.88, "signature_present": 0.95},
            }
        )

        results = extract_tier3(
            SCANNED_PDF, ["brand_name", "signature_present", "foreign_translations"], client=client
        )

        assert results["brand_name"].value == "Sample Creek"
        assert results["brand_name"].confidence == 0.88
        assert results["brand_name"].extraction_method == "ai_vision"
        assert results["brand_name"].bbox is None
        assert results["brand_name"].location_hint == LOCATION_HINTS["brand_name"]

        assert results["signature_present"].value is True
        assert results["signature_present"].confidence == 0.95

        # Null values from Claude are treated as unresolved, not included.
        assert "foreign_translations" not in results

    def test_handles_markdown_fenced_response(self):
        client = _mock_client({"values": {"brand_name": "Sample Creek"}, "confidence_scores": {}})
        client.messages.create.return_value.content[0].text = (
            "```json\n" + json.dumps({"values": {"brand_name": "Sample Creek"}, "confidence_scores": {}}) + "\n```"
        )

        results = extract_tier3(SCANNED_PDF, ["brand_name"], client=client)
        assert results["brand_name"].value == "Sample Creek"
        assert results["brand_name"].confidence == 0.75  # default when absent from confidence_scores

    def test_call_failure_returns_empty(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("API error")
        assert extract_tier3(SCANNED_PDF, ["brand_name"], client=client) == {}

    def test_system_prompt_uses_cache_control(self):
        client = _mock_client({"values": {}, "confidence_scores": {}})
        extract_tier3(SCANNED_PDF, ["brand_name"], client=client)
        _, kwargs = client.messages.create.call_args
        assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


# ---------------------------------------------------------------------------
# Tiered fallback ordering (run_stage3_extraction)
# ---------------------------------------------------------------------------


class TestRunStage3Extraction:
    def test_acroform_resolved_entirely_by_tier1(self):
        results = run_stage3_extraction(ACROFORM_PDF, client=None)

        resolved_fields = (
            "brand_name",
            "fanciful_name",
            "applicant_name",
            "applicant_address",
            "source",
            "product_type",
            "serial_number",
            "phone_number",
            "email_address",
            "embossed_info",
            "date_of_application",
            "applicant_printed_name",
            "plant_registry_number",
            "application_type",
        )
        for field in resolved_fields:
            assert results[field].extraction_method == "acroform"
            assert results[field].value is not None

        # Genuinely empty fields remain unresolved without Tier 3 (no API key).
        for field in ("representative_id", "mailing_address", "formula_id", "grape_varietals", "wine_appellation"):
            assert results[field].extraction_method is None
            assert results[field].value is None
            assert results[field].location_hint == LOCATION_HINTS[field]

    def test_flattened_falls_back_to_tier2(self):
        results = run_stage3_extraction(FLATTENED_PDF, client=None)

        resolved_fields = (
            "brand_name",
            "fanciful_name",
            "applicant_name",
            "applicant_address",
            "phone_number",
            "email_address",
            "embossed_info",
            "date_of_application",
            "applicant_printed_name",
            "plant_registry_number",
            "serial_number",
        )
        for field in resolved_fields:
            assert results[field].extraction_method == "pdftext"
            assert results[field].value is not None

        # Checkbox-derived fields aren't resolvable by Tier1 (no AcroForm) or
        # Tier2 (never attempted) without Tier 3.
        for field in ("source", "product_type", "application_type", "signature_present", "foreign_translations"):
            assert results[field].extraction_method is None

    def test_scanned_falls_back_to_tier3(self):
        stub_values = {field: "stub-value" for field in PART_I_FIELDS if field != "application_type"}
        client = _mock_client({"values": stub_values, "confidence_scores": {}})

        results = run_stage3_extraction(SCANNED_PDF, client=client)

        assert results["brand_name"].value == "stub-value"
        assert results["brand_name"].extraction_method == "ai_vision"
        assert results["brand_name"].confidence == 0.75

        # Tier 3 is called exactly once, requesting every Part I field.
        client.messages.create.assert_called_once()
        _, kwargs = client.messages.create.call_args
        requested = kwargs["messages"][0]["content"][1]["text"]
        for field in PART_I_FIELDS:
            assert field in requested

    def test_every_field_has_a_result_with_confidence_or_hint(self):
        results = run_stage3_extraction(SCANNED_PDF, client=None)

        assert set(results.keys()) == set(PART_I_FIELDS)
        for field, fr in results.items():
            assert fr.value is None
            assert fr.confidence is None
            assert fr.extraction_method is None
            assert fr.location_hint == LOCATION_HINTS[field]


# ---------------------------------------------------------------------------
# 5.6 — Persistence
# ---------------------------------------------------------------------------


class TestPersistFormParameters:
    def test_persists_results_and_updates_application(self, db_session):
        from models.application import Application
        from models.form_parameter import FormParameter

        application = Application(status="PENDING")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        results = run_stage3_extraction(ACROFORM_PDF, client=None)
        persist_form_parameters(db_session, application, results)

        assert application.status == "FORM_ASSESSED"
        assert application.brand_name == "Sample Creek"
        assert application.applicant_name == "Sample Creek Distillery, LLC"
        assert application.product_type == "distilled_spirits"
        assert application.source == "domestic"
        assert application.serial_number == "26-1"
        assert application.year == "26"
        assert application.application_type == "14a"

        params = db_session.query(FormParameter).filter(FormParameter.application_id == application.id).all()
        assert len(params) == len(PART_I_FIELDS)

        by_field = {p.field_name: p for p in params}
        assert by_field["brand_name"].field_value == "Sample Creek"
        assert by_field["brand_name"].confidence == 1.0
        assert by_field["brand_name"].extraction_method == "acroform"
        assert json.loads(by_field["brand_name"].bbox_json)["w"] == 224.2

        assert by_field["grape_varietals"].field_value is None
        assert by_field["grape_varietals"].location_hint == LOCATION_HINTS["grape_varietals"]

        app_type = json.loads(by_field["application_type"].field_value)
        assert app_type["checked"] == ["14a"]

    def test_replaces_existing_parameters(self, db_session):
        from models.application import Application
        from models.form_parameter import FormParameter

        application = Application(status="PENDING")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        results = run_stage3_extraction(ACROFORM_PDF, client=None)
        persist_form_parameters(db_session, application, results)
        persist_form_parameters(db_session, application, results)

        params = db_session.query(FormParameter).filter(FormParameter.application_id == application.id).all()
        assert len(params) == len(PART_I_FIELDS)

    def test_preserves_upload_time_values_when_unresolved(self, db_session):
        from models.application import Application

        application = Application(status="PENDING", brand_name="Upload-Time Brand")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        results = run_stage3_extraction(SCANNED_PDF, client=None)  # all fields unresolved
        persist_form_parameters(db_session, application, results)

        assert application.brand_name == "Upload-Time Brand"
        assert application.status == "FORM_ASSESSED"

"""Stage 4 (Label Assessment, TS-02) extraction tests (WBS 6.8)."""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import cv2
import pytesseract
import pytest

from services import settings_service
from services.label_extraction import (
    GOVERNMENT_WARNING_TEXT,
    LABEL_FIELDS,
    LOCATION_HINTS,
    SIMPLE_FIELDS,
    LabelFieldResult,
    _decode_image,
    _estimate_skew_angle,
    compute_header_height_ratio,
    deskew,
    extract_label_fields,
    fuzzy_match_bbox,
    normalize_contrast,
    persist_label_parameters,
    preprocess_image,
    run_ocr,
    run_stage4_extraction,
    suppress_glare,
)

TESTDATA = Path(__file__).resolve().parent.parent.parent / "testdata"
DEGRADED = TESTDATA / "degraded"


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
# 6.1 — OpenCV preprocessing (FR-039), against WBS 2.6 degraded fixtures
# ---------------------------------------------------------------------------


class TestPreprocessing:
    def test_deskew_corrects_rotation(self):
        img = _decode_image((DEGRADED / "woodford_front_angle.jpg").read_bytes())
        angle_before = abs(_estimate_skew_angle(img))
        angle_after = abs(_estimate_skew_angle(deskew(img)))

        assert angle_before > 5  # fixture is rotated ~8 degrees
        assert angle_after < 1
        assert angle_after < angle_before

    def test_deskew_combined_fixture(self):
        """FR-039 acceptance test: glare + rotation, deskew still corrects orientation."""
        img = _decode_image((DEGRADED / "woodford_front_combined.jpg").read_bytes())
        angle_before = abs(_estimate_skew_angle(img))
        angle_after = abs(_estimate_skew_angle(deskew(img)))

        assert angle_after < angle_before

    def test_suppress_glare_reduces_blowout(self):
        img = _decode_image((DEGRADED / "woodford_front_glare.jpg").read_bytes())
        gray_before = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        before = int((gray_before >= 250).sum())

        suppressed = suppress_glare(img)
        gray_after = cv2.cvtColor(suppressed, cv2.COLOR_BGR2GRAY)
        after = int((gray_after >= 250).sum())

        assert after < before

    def test_normalize_contrast_increases_spread(self):
        img = _decode_image((DEGRADED / "woodford_front_lowlight.jpg").read_bytes())
        gray_before = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        normalized = normalize_contrast(img)
        gray_after = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)

        assert gray_after.std() > gray_before.std()

    def test_preprocess_image_combined_runs_full_pipeline(self):
        raw = (DEGRADED / "woodford_front_combined.jpg").read_bytes()
        raw_img = _decode_image(raw)

        out_bytes = preprocess_image(raw)
        out_img = _decode_image(out_bytes)

        assert out_img.shape[:2] == raw_img.shape[:2]
        angle_before = abs(_estimate_skew_angle(raw_img))
        angle_after = abs(_estimate_skew_angle(out_img))
        assert angle_after < angle_before


# ---------------------------------------------------------------------------
# 6.2/6.3 — Claude Vision extraction + Government Warning detection (FR-030-035)
# ---------------------------------------------------------------------------


class TestExtraction:
    def test_parses_simple_fields(self):
        payload = {
            "values": {
                "brand_name": {"value": "Woodford Reserve", "confidence": 0.98, "location_hint": "top-center"},
                "alcohol_content": {"value": "45.2% Alc./Vol.", "confidence": 0.95, "location_hint": "front-bottom"},
                "other_text": [],
            }
        }
        results = extract_label_fields(b"fake-bytes", client=_mock_client(payload))

        assert results["brand_name"][0].value == "Woodford Reserve"
        assert results["brand_name"][0].confidence == 0.98
        assert results["brand_name"][0].location_hint == "top-center"
        assert results["alcohol_content"][0].value == "45.2% Alc./Vol."

        # Fields with no element on this image -> value None with fallback location_hint (FR-011).
        assert results["fanciful_name"][0].value is None
        assert results["fanciful_name"][0].location_hint == LOCATION_HINTS["fanciful_name"]

    def test_government_warning_exact_match_true(self):
        payload = {
            "values": {
                "government_warning": {
                    "text_present": True,
                    "text_found": GOVERNMENT_WARNING_TEXT,
                    "header_all_caps": True,
                    "header_bold": True,
                    "confidence": 0.99,
                    "location_hint": "bottom",
                }
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload))
        gw = results["government_warning"][0].value

        assert gw["text_present"] is True
        assert gw["header_all_caps"] is True
        assert gw["header_bold"] is True
        assert gw["text_exact_match"] is True

    def test_government_warning_paraphrased_fails_exact_match(self):
        payload = {
            "values": {
                "government_warning": {
                    "text_present": True,
                    "text_found": "Government Warning: Drinking may cause health problems.",
                    "header_all_caps": False,
                    "header_bold": True,
                    "confidence": 0.9,
                    "location_hint": "bottom",
                }
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload))
        gw = results["government_warning"][0].value

        assert gw["header_all_caps"] is False
        assert gw["text_exact_match"] is False

    def test_government_warning_absent(self):
        payload = {
            "values": {
                "government_warning": {
                    "text_present": False,
                    "text_found": None,
                    "header_all_caps": None,
                    "header_bold": None,
                    "confidence": 0.0,
                    "location_hint": "n/a",
                }
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload))
        gw = results["government_warning"][0].value

        assert gw["text_present"] is False
        assert gw["text_found"] is None
        assert gw["text_exact_match"] is None

    def test_other_text_catch_all(self):
        payload = {
            "values": {
                "other_text": [
                    {"value": "UPC: 012345678905", "confidence": 0.9, "location_hint": "bottom-right"},
                    {"value": "Contains Sulfites", "confidence": 0.85, "location_hint": "back, small print"},
                ]
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload))

        assert len(results["other_text"]) == 2
        assert results["other_text"][0].value == "UPC: 012345678905"
        assert results["other_text"][1].location_hint == "back, small print"

    def test_no_client_returns_skeleton(self, monkeypatch):
        monkeypatch.setattr(settings_service, "is_configured", lambda: False)

        results = extract_label_fields(b"x")

        for field in SIMPLE_FIELDS:
            assert results[field][0].value is None
            assert results[field][0].location_hint == LOCATION_HINTS[field]
        assert results["government_warning"][0].value["text_present"] is False
        assert results["other_text"] == []

    def test_handles_exception(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("boom")

        results = extract_label_fields(b"x", client=client)

        assert results["brand_name"][0].value is None


# ---------------------------------------------------------------------------
# 6.4/6.5 — OCR fuzzy-match + header_height_ratio (FR-040)
# ---------------------------------------------------------------------------


class TestOcrFuzzyMatch:
    def test_fuzzy_match_bbox_multi_word(self):
        ocr_words = [
            {"text": "WOODFORD", "x": 10, "y": 10, "w": 100, "h": 20},
            {"text": "RESERVE", "x": 115, "y": 10, "w": 90, "h": 20},
            {"text": "BOURBON", "x": 10, "y": 40, "w": 100, "h": 18},
        ]
        bbox = fuzzy_match_bbox("Woodford Reserve", ocr_words)
        assert bbox == {"x": 10, "y": 10, "w": 195, "h": 20}

    def test_fuzzy_match_bbox_no_match_returns_none(self):
        ocr_words = [{"text": "RANDOM", "x": 0, "y": 0, "w": 50, "h": 10}]
        assert fuzzy_match_bbox("Completely Different Phrase", ocr_words) is None

    def test_fuzzy_match_bbox_empty_inputs(self):
        assert fuzzy_match_bbox("", [{"text": "X", "x": 0, "y": 0, "w": 1, "h": 1}]) is None
        assert fuzzy_match_bbox("value", []) is None

    def test_compute_header_height_ratio(self):
        """FR-040 example: header twice the height of body text -> ratio ~= 2.0."""
        ocr_words = [
            {"text": "GOVERNMENT", "x": 10, "y": 100, "w": 150, "h": 20},
            {"text": "WARNING:", "x": 165, "y": 100, "w": 100, "h": 20},
            {"text": "According", "x": 10, "y": 130, "w": 70, "h": 10},
            {"text": "to", "x": 85, "y": 130, "w": 20, "h": 10},
            {"text": "the", "x": 110, "y": 130, "w": 25, "h": 10},
        ]
        assert compute_header_height_ratio(ocr_words) == 2.0

    def test_compute_header_height_ratio_no_header(self):
        ocr_words = [{"text": "RANDOM", "x": 0, "y": 0, "w": 50, "h": 10}]
        assert compute_header_height_ratio(ocr_words) is None

    def test_compute_header_height_ratio_no_words(self):
        assert compute_header_height_ratio([]) is None

    def test_run_ocr_returns_list(self):
        """Real call (Tesseract may or may not be installed) -> never raises."""
        image_bytes = (TESTDATA / "Woodford Reserve burbon front.jpg").read_bytes()
        assert isinstance(run_ocr(image_bytes), list)

    def test_run_ocr_handles_tesseract_not_found(self, monkeypatch):
        """WBS.md Note 7 contingency #1: missing Tesseract degrades to []."""

        def _raise(*args, **kwargs):
            raise pytesseract.TesseractNotFoundError()

        monkeypatch.setattr(pytesseract, "image_to_data", _raise)

        image_bytes = (TESTDATA / "Woodford Reserve burbon front.jpg").read_bytes()
        assert run_ocr(image_bytes) == []


# ---------------------------------------------------------------------------
# 6.6/6.7 — per-image concurrency + persistence (FR-038, IA-19/IA-24)
# ---------------------------------------------------------------------------


class TestOrchestrationAndPersistence:
    def test_run_stage4_extraction_processes_all_images(self, db_session):
        from models.application import Application
        from models.label_image import LabelImage

        application = Application(brand_name="Woodford Reserve")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        img1 = LabelImage(
            application_id=application.id,
            image_path=str(TESTDATA / "Woodford Reserve burbon front.jpg"),
            label_type="brand",
        )
        img2 = LabelImage(
            application_id=application.id,
            image_path=str(TESTDATA / "Woodford Reserve burbon back.jpg"),
            label_type="back",
        )
        db_session.add_all([img1, img2])
        db_session.commit()
        db_session.refresh(img1)
        db_session.refresh(img2)

        payload = {
            "values": {
                "brand_name": {"value": "Woodford Reserve", "confidence": 0.95, "location_hint": "top-center"},
            }
        }
        client = _mock_client(payload)

        results = asyncio.run(run_stage4_extraction([img1, img2], client=client))

        assert set(results.keys()) == {img1.id, img2.id}
        for field_results in results.values():
            for field in LABEL_FIELDS:
                assert field in field_results
            assert field_results["brand_name"][0].value == "Woodford Reserve"

    def test_persist_label_parameters(self, db_session):
        from models.application import Application
        from models.label_parameter import LabelParameter

        application = Application(brand_name="Test Brand")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        results_by_image = {
            1: {
                "brand_name": [
                    LabelFieldResult("Test Brand", 0.9, "top-center", bbox={"x": 1, "y": 2, "w": 3, "h": 4})
                ],
                "government_warning": [
                    LabelFieldResult(
                        {
                            "text_found": GOVERNMENT_WARNING_TEXT,
                            "text_present": True,
                            "header_all_caps": True,
                            "header_bold": True,
                            "text_exact_match": True,
                        },
                        0.95,
                        "bottom",
                        header_height_ratio=2.0,
                    )
                ],
                "other_text": [
                    LabelFieldResult("UPC: 012345", 0.8, "bottom-right"),
                    LabelFieldResult("Contains Sulfites", 0.7, "back"),
                ],
            }
        }

        persist_label_parameters(db_session, application, results_by_image)

        rows = db_session.query(LabelParameter).filter(LabelParameter.application_id == application.id).all()
        by_field: dict[str, list[LabelParameter]] = {}
        for row in rows:
            by_field.setdefault(row.field_name, []).append(row)

        assert by_field["brand_name"][0].field_value == "Test Brand"
        assert by_field["brand_name"][0].label_image_id == 1
        assert json.loads(by_field["brand_name"][0].bbox_json) == {"x": 1, "y": 2, "w": 3, "h": 4}

        gw_row = by_field["government_warning"][0]
        gw_value = json.loads(gw_row.field_value)
        assert gw_value["text_exact_match"] is True
        assert gw_row.header_height_ratio == 2.0

        assert len(by_field["other_text"]) == 2
        assert application.status == "LABEL_ASSESSED"

"""Stage 4 (Label Assessment, TS-02) extraction tests (WBS 6.8)."""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import cv2
import numpy as np
import pytesseract
import pytest

from services import settings_service
from services.label_extraction import (
    GOVERNMENT_WARNING_TEXT,
    HEADER_BOLD_STROKE_RATIO_THRESHOLD,
    LABEL_FIELDS,
    LOCATION_HINTS,
    MAX_GLARE_AREA_FRACTION,
    SIMPLE_FIELDS,
    LabelFieldResult,
    _claude_bbox_to_pixels,
    _decode_image,
    _estimate_skew_angle,
    _process_label_image,
    compute_header_height_ratio,
    compute_header_stroke_ratio,
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

    def test_suppress_glare_reduces_localized_blowout(self):
        """A small, localized glare hot-spot (camera-flash reflection) on an
        otherwise dark/colored label is inpainted away."""
        img = np.full((200, 200, 3), 60, dtype=np.uint8)
        cv2.circle(img, (100, 100), 15, (255, 255, 255), -1)  # ~1.8% of the image

        gray_before = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        before = int((gray_before >= 250).sum())

        suppressed = suppress_glare(img)
        gray_after = cv2.cvtColor(suppressed, cv2.COLOR_BGR2GRAY)
        after = int((gray_after >= 250).sum())

        assert after < before

    def test_suppress_glare_skips_large_bright_regions(self):
        """A predominantly white/light label background must be left alone --
        inpainting over it destroys legible text instead of removing glare
        (regression: real wine labels with white backgrounds were being
        reduced to illegible blotches)."""
        img = _decode_image((DEGRADED / "woodford_front_glare.jpg").read_bytes())
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        assert (gray >= 235).sum() / gray.size > MAX_GLARE_AREA_FRACTION  # fixture sanity check

        suppressed = suppress_glare(img)

        assert np.array_equal(suppressed, img)

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
        client = _mock_client(payload)
        results = extract_label_fields(b"fake-bytes", client=client)

        assert results["brand_name"][0].value == "Woodford Reserve"
        assert results["brand_name"][0].confidence == 0.98
        assert results["brand_name"][0].location_hint == "top-center"
        assert results["alcohol_content"][0].value == "45.2% Alc./Vol."

        # Fields with no element on this image -> value None with fallback location_hint (FR-011).
        assert results["fanciful_name"][0].value is None
        assert results["fanciful_name"][0].location_hint == LOCATION_HINTS["fanciful_name"]

        # temperature=0 (FR-035 tuning): Claude's header_bold/header_all_caps
        # flags proved non-deterministic across repeated calls on the same
        # image at the default temperature.
        assert client.messages.create.call_args.kwargs["temperature"] == 0

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
# 6.5 (cont.) — header_stroke_ratio (FR-040, corroborates FR-035's "bold")
# ---------------------------------------------------------------------------


class TestHeaderStrokeRatio:
    """`compute_header_stroke_ratio` measures stroke *weight*, not glyph size,
    so it can corroborate "bold" even when header and body text are the same
    height (header_height_ratio == 1.0)."""

    @staticmethod
    def _canvas() -> np.ndarray:
        return np.full((200, 400), 255, dtype=np.uint8)

    def test_bold_header_yields_ratio_above_one(self):
        gray = self._canvas()
        # Header: thick strokes. Body: thin strokes. Same glyph size.
        cv2.rectangle(gray, (10, 10), (150, 40), 0, thickness=6)
        cv2.rectangle(gray, (10, 80), (150, 110), 0, thickness=1)
        cv2.rectangle(gray, (10, 130), (150, 160), 0, thickness=1)
        ocr_words = [
            {"text": "GOVERNMENT", "x": 10, "y": 10, "w": 140, "h": 30},
            {"text": "WARNING:", "x": 10, "y": 80, "w": 140, "h": 30},
            {"text": "ACCORDING", "x": 10, "y": 130, "w": 140, "h": 30},
        ]
        ratio = compute_header_stroke_ratio(gray, ocr_words, header_text="GOVERNMENT")
        assert ratio > HEADER_BOLD_STROKE_RATIO_THRESHOLD

    def test_thin_header_yields_ratio_below_threshold(self):
        gray = self._canvas()
        # Header: thin strokes. Body: thick strokes. Same glyph size.
        cv2.rectangle(gray, (10, 10), (150, 40), 0, thickness=1)
        cv2.rectangle(gray, (10, 80), (150, 110), 0, thickness=6)
        cv2.rectangle(gray, (10, 130), (150, 160), 0, thickness=6)
        ocr_words = [
            {"text": "GOVERNMENT", "x": 10, "y": 10, "w": 140, "h": 30},
            {"text": "WARNING:", "x": 10, "y": 80, "w": 140, "h": 30},
            {"text": "ACCORDING", "x": 10, "y": 130, "w": 140, "h": 30},
        ]
        ratio = compute_header_stroke_ratio(gray, ocr_words, header_text="GOVERNMENT")
        assert ratio < HEADER_BOLD_STROKE_RATIO_THRESHOLD

    def test_no_header_match_returns_none(self):
        gray = self._canvas()
        ocr_words = [{"text": "RANDOM", "x": 10, "y": 10, "w": 140, "h": 30}]
        assert compute_header_stroke_ratio(gray, ocr_words, header_text="GOVERNMENT") is None

    def test_no_words_returns_none(self):
        gray = self._canvas()
        assert compute_header_stroke_ratio(gray, []) is None


# ---------------------------------------------------------------------------
# 6.5 (cont.) — Claude-provided bbox as fallback for OCR-illegible text (FR-040)
# ---------------------------------------------------------------------------


class TestClaudeBboxFallback:
    def test_converts_normalized_region_to_pixels(self):
        assert _claude_bbox_to_pixels({"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.25}, 1000, 2000) == {
            "x": 100,
            "y": 400,
            "w": 300,
            "h": 500,
        }

    def test_clamps_region_that_overflows_image_bounds(self):
        result = _claude_bbox_to_pixels({"x": 0.9, "y": 0.9, "w": 0.5, "h": 0.5}, 1000, 1000)
        assert result == {"x": 900, "y": 900, "w": 100, "h": 100}

    @pytest.mark.parametrize(
        "bbox",
        [
            None,
            "not a dict",
            {"x": 0.1, "y": 0.2, "w": 0.3},  # missing "h"
            {"x": 1.5, "y": 0.2, "w": 0.3, "h": 0.1},  # x out of 0-1 range
            {"x": 0.1, "y": 0.2, "w": 0, "h": 0.1},  # zero width
            {"x": "bad", "y": 0.2, "w": 0.3, "h": 0.1},  # non-numeric
        ],
    )
    def test_rejects_malformed_region(self, bbox):
        assert _claude_bbox_to_pixels(bbox, 1000, 1000) is None

    def test_returns_none_without_image_dimensions(self):
        assert _claude_bbox_to_pixels({"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.1}, None, None) is None

    def test_extract_label_fields_converts_bbox_when_dimensions_given(self):
        payload = {
            "values": {
                "brand_name": {
                    "value": "Barrilito",
                    "confidence": 0.9,
                    "location_hint": "top-center",
                    "bbox": {"x": 0.1, "y": 0.05, "w": 0.4, "h": 0.1},
                },
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload), img_w=1000, img_h=2000)

        assert results["brand_name"][0].bbox == {"x": 100, "y": 100, "w": 400, "h": 200}

    def test_extract_label_fields_omits_bbox_without_dimensions(self):
        payload = {
            "values": {
                "brand_name": {
                    "value": "Barrilito",
                    "confidence": 0.9,
                    "location_hint": "top-center",
                    "bbox": {"x": 0.1, "y": 0.05, "w": 0.4, "h": 0.1},
                },
            }
        }
        results = extract_label_fields(b"x", client=_mock_client(payload))

        assert results["brand_name"][0].bbox is None

    def test_process_label_image_uses_claude_bbox_when_ocr_has_no_match(self, db_session, monkeypatch):
        """Stylized/logo text (e.g. 'BARRILITO') that Tesseract can't read at all
        still gets a (generous, approximate) bbox from Claude's region estimate."""
        from models.application import Application
        from models.label_image import LabelImage
        from services import label_extraction

        application = Application(brand_name="Test")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        image_path = TESTDATA / "Woodford Reserve burbon front.jpg"
        label_image = LabelImage(application_id=application.id, image_path=str(image_path), label_type="brand")
        db_session.add(label_image)
        db_session.commit()
        db_session.refresh(label_image)

        img_h, img_w = _decode_image(image_path.read_bytes()).shape[:2]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: [])

        payload = {
            "values": {
                "brand_name": {
                    "value": "Barrilito",
                    "confidence": 0.9,
                    "location_hint": "top-center",
                    "bbox": {"x": 0.1, "y": 0.05, "w": 0.4, "h": 0.1},
                },
            }
        }
        results = asyncio.run(_process_label_image(label_image, client=_mock_client(payload)))

        assert results["brand_name"][0].bbox == _claude_bbox_to_pixels(
            payload["values"]["brand_name"]["bbox"], img_w, img_h
        )

    def test_process_label_image_ocr_match_overrides_claude_bbox(self, db_session, monkeypatch):
        """When OCR *can* find the text, its pixel-precise bbox wins over Claude's estimate."""
        from models.application import Application
        from models.label_image import LabelImage
        from services import label_extraction

        application = Application(brand_name="Test")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        image_path = TESTDATA / "Woodford Reserve burbon front.jpg"
        label_image = LabelImage(application_id=application.id, image_path=str(image_path), label_type="brand")
        db_session.add(label_image)
        db_session.commit()
        db_session.refresh(label_image)

        ocr_words = [
            {"text": "WOODFORD", "x": 10, "y": 10, "w": 100, "h": 20},
            {"text": "RESERVE", "x": 115, "y": 10, "w": 90, "h": 20},
        ]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: ocr_words)

        payload = {
            "values": {
                "brand_name": {
                    "value": "Woodford Reserve",
                    "confidence": 0.9,
                    "location_hint": "top-center",
                    "bbox": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},  # deliberately whole-image
                },
            }
        }
        results = asyncio.run(_process_label_image(label_image, client=_mock_client(payload)))

        assert results["brand_name"][0].bbox == {"x": 10, "y": 10, "w": 195, "h": 20}


# ---------------------------------------------------------------------------
# 6.6 (cont.) — OCR stroke-ratio corroboration of Claude's header_bold (FR-035)
# ---------------------------------------------------------------------------


class TestHeaderBoldCorroboration:
    """Claude's `header_bold` flag (FR-035) has proven non-deterministic across
    repeated Stage 4 calls on the same image -- the same "GOVERNMENT WARNING:"
    header was assessed True on one run and False on the next. When OCR shows
    the header's stroke weight is not lighter than body text, that
    corroborates "bold" and promotes a False/null flag to True so a single
    noisy call doesn't drive a HARD_FAILURE (FR-055)."""

    GW_PAYLOAD = {
        "values": {
            "government_warning": {
                "text_present": True,
                "text_found": GOVERNMENT_WARNING_TEXT,
                "header_all_caps": True,
                "header_bold": False,
                "confidence": 0.9,
                "location_hint": "bottom",
            }
        }
    }

    def _label_image(self, db_session):
        from models.application import Application
        from models.label_image import LabelImage

        application = Application(brand_name="Test")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        label_image = LabelImage(
            application_id=application.id,
            image_path=str(TESTDATA / "Woodford Reserve burbon front.jpg"),
            label_type="back",
        )
        db_session.add(label_image)
        db_session.commit()
        db_session.refresh(label_image)
        return label_image

    def test_promotes_header_bold_when_stroke_ratio_corroborates(self, db_session, monkeypatch):
        from services import label_extraction

        label_image = self._label_image(db_session)
        ocr_words = [{"text": "GOVERNMENT WARNING:", "x": 10, "y": 10, "w": 140, "h": 30}]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: ocr_words)
        monkeypatch.setattr(label_extraction, "compute_header_stroke_ratio", lambda *_a, **_k: 1.5)

        results = asyncio.run(_process_label_image(label_image, client=_mock_client(self.GW_PAYLOAD)))

        assert results["government_warning"][0].value["header_bold"] is True

    def test_does_not_promote_header_bold_when_stroke_ratio_below_threshold(self, db_session, monkeypatch):
        from services import label_extraction

        label_image = self._label_image(db_session)
        ocr_words = [{"text": "GOVERNMENT WARNING:", "x": 10, "y": 10, "w": 140, "h": 30}]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: ocr_words)
        monkeypatch.setattr(label_extraction, "compute_header_stroke_ratio", lambda *_a, **_k: 0.5)

        results = asyncio.run(_process_label_image(label_image, client=_mock_client(self.GW_PAYLOAD)))

        assert results["government_warning"][0].value["header_bold"] is False

    def test_does_not_promote_header_bold_when_stroke_ratio_none(self, db_session, monkeypatch):
        from services import label_extraction

        label_image = self._label_image(db_session)
        ocr_words = [{"text": "GOVERNMENT WARNING:", "x": 10, "y": 10, "w": 140, "h": 30}]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: ocr_words)
        monkeypatch.setattr(label_extraction, "compute_header_stroke_ratio", lambda *_a, **_k: None)

        results = asyncio.run(_process_label_image(label_image, client=_mock_client(self.GW_PAYLOAD)))

        assert results["government_warning"][0].value["header_bold"] is False

    def test_skips_stroke_ratio_when_claude_already_says_bold(self, db_session, monkeypatch):
        """No need to spend the extra OCR/CV pass when Claude already said True."""
        from services import label_extraction

        label_image = self._label_image(db_session)
        ocr_words = [{"text": "GOVERNMENT WARNING:", "x": 10, "y": 10, "w": 140, "h": 30}]
        monkeypatch.setattr(label_extraction, "run_ocr", lambda *_a, **_k: ocr_words)

        def _boom(*_a, **_k):
            raise AssertionError("compute_header_stroke_ratio should not be called")

        monkeypatch.setattr(label_extraction, "compute_header_stroke_ratio", _boom)

        payload = json.loads(json.dumps(self.GW_PAYLOAD))
        payload["values"]["government_warning"]["header_bold"] = True

        results = asyncio.run(_process_label_image(label_image, client=_mock_client(payload)))

        assert results["government_warning"][0].value["header_bold"] is True


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

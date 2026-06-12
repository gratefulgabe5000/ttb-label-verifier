"""Stage 4: Label Assessment — OpenCV preprocessing + Claude Vision + OCR bbox assist (TS-02).

For every label image: (1) OpenCV preprocessing (deskew/perspective correction,
CLAHE contrast normalization, glare suppression — FR-039) runs before the image
is sent to Claude; (2) Claude Vision extracts every mandatory (FR-031), secondary
(FR-032), and other (FR-033) label element in one pass, including the Government
Warning text and its formatting (FR-034/035); (3) concurrently, Tesseract OCR
(FR-040) produces word-level text + bounding boxes, which are fuzzy-matched
against Claude's extracted values to recover a pixel `bbox` for each element and,
for `government_warning`, a `header_height_ratio`. Per label image these run
concurrently via `asyncio.gather` (IA-19/IA-24); if Tesseract is unavailable,
OCR degrades to `[]` and bboxes fall back to `location_hint` (WBS.md Note 7,
contingency #1) without blocking 6.1-6.3/6.6-6.8.
"""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytesseract
from anthropic import Anthropic
from sqlalchemy.orm import Session

from models.application import Application
from models.label_image import LabelImage
from models.label_parameter import LabelParameter
from services import settings_service

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical Stage 4 output fields (DevLog §3.2, FR-031/032).
MANDATORY_FIELDS = [
    "brand_name",
    "fanciful_name",
    "class_type_designation",
    "alcohol_content",
    "net_contents",
    "bottler_name",
    "bottler_address",
    "country_of_origin",
]
SECONDARY_FIELDS = [
    "grape_varietals",
    "wine_appellation",
    "vintage_date",
    "age_statement",
    "for_sale_in_state",
]
SIMPLE_FIELDS = MANDATORY_FIELDS + SECONDARY_FIELDS
# "government_warning" (dict value) and "other_text" (list value) are special-cased.
LABEL_FIELDS = [*SIMPLE_FIELDS, "government_warning", "other_text"]

# Human-readable fallback locations (IA-13) when no OCR bbox match is found.
LOCATION_HINTS = {
    "brand_name": "front label, prominent placement",
    "fanciful_name": "front label, near brand name",
    "class_type_designation": "front label, below brand name",
    "alcohol_content": "front or back label",
    "net_contents": "front label, near bottom or neck",
    "bottler_name": "back label",
    "bottler_address": "back label, near bottler name",
    "country_of_origin": "back label (imported products)",
    "government_warning": "back label, bottom area",
    "grape_varietals": "front or back label",
    "wine_appellation": "front label, near brand name",
    "vintage_date": "front label",
    "age_statement": "front label, near brand or class/type",
    "for_sale_in_state": "back label",
    "other_text": "anywhere on label",
}

# Statutory Government Warning text (27 CFR § 16.21, DevLog §2.2), whitespace-collapsed.
GOVERNMENT_WARNING_TEXT = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. (2) "
    "Consumption of alcoholic beverages impairs your ability to drive a car or operate "
    "machinery, and may cause health problems."
)

# Static system prompt for Stage 4 Claude Vision (cache_control, IA-25).
STAGE4_SYSTEM_PROMPT = """You are a data-extraction assistant for the Alcohol and Tobacco Tax and \
Trade Bureau (TTB). You will be shown a photo of one panel (front, back, neck, \
or other) of an alcohol beverage label, submitted as part of a Certificate of \
Label Approval (COLA) application.

Carefully read every piece of text visible on this image and extract it into \
structured JSON. Respond with ONLY a single JSON object (no markdown fences, \
no commentary) with this shape:

{
  "values": {
    "brand_name": {"value": "<string or null>", "confidence": <0.0-1.0>, "location_hint": "<short position, e.g. 'top-center'>"},
    "fanciful_name": {"value": "<string or null>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "class_type_designation": {"value": "<string or null, e.g. 'Kentucky Straight Bourbon Whiskey'>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "alcohol_content": {"value": "<string or null, e.g. '40% Alc./Vol. (80 Proof)'>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "net_contents": {"value": "<string or null, e.g. '750 mL'>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "bottler_name": {"value": "<string or null>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "bottler_address": {"value": "<string or null>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "country_of_origin": {"value": "<string or null, imported products only>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "grape_varietals": {"value": "<string or null, comma-separated, wine only>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "wine_appellation": {"value": "<string or null, wine only>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "vintage_date": {"value": "<string or null, wine only>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "age_statement": {"value": "<string or null, e.g. 'Aged 12 Years'>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "for_sale_in_state": {"value": "<string or null, e.g. 'FOR SALE IN PENNSYLVANIA ONLY'>", "confidence": <0.0-1.0>, "location_hint": "<...>"},
    "government_warning": {
      "text_present": <true|false>,
      "text_found": "<exact transcription of the Government Warning text on this image, or null>",
      "header_all_caps": <true|false|null, "is 'GOVERNMENT WARNING:' rendered in all capital letters?">,
      "header_bold": <true|false|null, "is 'GOVERNMENT WARNING:' rendered in bold type?">,
      "confidence": <0.0-1.0>,
      "location_hint": "<...>"
    },
    "other_text": [
      {"value": "<any other text visible on this image, e.g. UPC code, allergen statement>", "confidence": <0.0-1.0>, "location_hint": "<...>"}
    ]
  }
}

Use null for any field with no corresponding element on this image. Do not \
guess at text that is not actually visible. `location_hint` should be a short \
relative description such as "top-left", "bottom-center", "neck label", etc. \
Transcribe `government_warning.text_found` exactly as printed, including \
punctuation and capitalization — do not paraphrase or correct it."""


def _normalize_for_comparison(text: str) -> str:
    return " ".join(text.split()).strip().lower()


@dataclass
class LabelFieldResult:
    """One field's Stage 4 result for a single label image, ready for `persist_label_parameters`."""

    value: Any
    confidence: float | None
    location_hint: str | None = None
    bbox: dict | None = None
    header_height_ratio: float | None = None


# ---------------------------------------------------------------------------
# 6.1 — OpenCV preprocessing (FR-039)
# ---------------------------------------------------------------------------


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return img


def _encode_image(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("Could not encode image")
    return buf.tobytes()


def _estimate_skew_angle(img: np.ndarray) -> float:
    """Estimate small rotation (degrees) via minAreaRect over non-background pixels."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] < 10:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if angle > 45:
        angle = angle - 90
    return float(angle)


def deskew(img: np.ndarray) -> np.ndarray:
    """Correct small rotation/perspective skew (FR-039)."""
    angle = _estimate_skew_angle(img)
    if abs(angle) < 0.5:
        return img
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
    return cv2.warpAffine(
        img, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def normalize_contrast(img: np.ndarray) -> np.ndarray:
    """CLAHE local contrast normalization on the luminance channel (FR-039)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def suppress_glare(img: np.ndarray) -> np.ndarray:
    """Detect blown-out highlights and inpaint them from surrounding pixels (FR-039)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    if cv2.countNonZero(mask) == 0:
        return img
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    return cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)


def preprocess_image(image_bytes: bytes) -> bytes:
    """Run the full FR-039 pipeline: deskew -> glare suppression -> contrast normalization."""
    img = _decode_image(image_bytes)
    img = deskew(img)
    img = suppress_glare(img)
    img = normalize_contrast(img)
    return _encode_image(img)


# ---------------------------------------------------------------------------
# 6.2/6.3 — Claude Vision extraction + Government Warning detection (FR-030-035)
# ---------------------------------------------------------------------------


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _empty_results() -> dict[str, list[LabelFieldResult]]:
    results: dict[str, list[LabelFieldResult]] = {}
    for field in SIMPLE_FIELDS:
        results[field] = [LabelFieldResult(None, None, LOCATION_HINTS.get(field))]
    results["government_warning"] = [
        LabelFieldResult(
            {
                "text_found": None,
                "text_present": False,
                "header_all_caps": None,
                "header_bold": None,
                "text_exact_match": None,
            },
            None,
            LOCATION_HINTS["government_warning"],
        )
    ]
    results["other_text"] = []
    return results


def _parse_label_fields(data: dict) -> dict[str, list[LabelFieldResult]]:
    results = _empty_results()
    values = data.get("values", {}) if isinstance(data, dict) else {}

    for field in SIMPLE_FIELDS:
        entry = values.get(field)
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if value in (None, "", []):
            continue
        results[field] = [
            LabelFieldResult(
                value=value,
                confidence=entry.get("confidence"),
                location_hint=entry.get("location_hint") or LOCATION_HINTS.get(field),
            )
        ]

    gw = values.get("government_warning")
    if isinstance(gw, dict):
        text_found = gw.get("text_found") or None
        text_present = gw.get("text_present")
        gw_value = {
            "text_found": text_found,
            "text_present": bool(text_present) if text_present is not None else (text_found is not None),
            "header_all_caps": gw.get("header_all_caps"),
            "header_bold": gw.get("header_bold"),
            "text_exact_match": (
                _normalize_for_comparison(text_found) == _normalize_for_comparison(GOVERNMENT_WARNING_TEXT)
                if text_found
                else None
            ),
        }
        results["government_warning"] = [
            LabelFieldResult(
                value=gw_value,
                confidence=gw.get("confidence"),
                location_hint=gw.get("location_hint") or LOCATION_HINTS["government_warning"],
            )
        ]

    other_text = values.get("other_text")
    if isinstance(other_text, list):
        results["other_text"] = [
            LabelFieldResult(
                value=item.get("value"),
                confidence=item.get("confidence"),
                location_hint=item.get("location_hint") or LOCATION_HINTS["other_text"],
            )
            for item in other_text
            if isinstance(item, dict) and item.get("value") not in (None, "")
        ]

    return results


def extract_label_fields(image_bytes: bytes, *, client: Anthropic | None = None) -> dict[str, list[LabelFieldResult]]:
    """Run the Stage 4 Claude Vision extraction prompt against one preprocessed label image.

    Returns an all-null skeleton (FR-011) if no API key is configured (IA-02)
    or if the call fails for any reason — never raises.
    """
    skeleton = _empty_results()

    if client is None:
        if not settings_service.is_configured():
            return skeleton
        client = Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=[{"type": "text", "text": STAGE4_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.standard_b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all label elements from this image as JSON, per the schema in your instructions.",
                        },
                    ],
                }
            ],
        )
        data = _parse_json_response(response.content[0].text)
    except Exception:
        return skeleton

    return _parse_label_fields(data)


# ---------------------------------------------------------------------------
# 6.4 — Tesseract OCR pass (FR-040)
# ---------------------------------------------------------------------------


def run_ocr(image_bytes: bytes) -> list[dict]:
    """Return word-level OCR boxes `{"text", "x", "y", "w", "h"}` (pixels, top-left origin).

    Returns `[]` if Tesseract is not installed or the call fails for any
    reason (WBS.md §4 Note 7 contingency #1) — bboxes then fall back to
    `location_hint` and `header_height_ratio` stays `None`.
    """
    try:
        img = _decode_image(image_bytes)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    except Exception:
        return []

    words: list[dict] = []
    for i, text in enumerate(data.get("text", [])):
        text = text.strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError, KeyError, IndexError):
            conf = -1.0
        if conf < 0:
            continue
        words.append(
            {
                "text": text,
                "x": int(data["left"][i]),
                "y": int(data["top"][i]),
                "w": int(data["width"][i]),
                "h": int(data["height"][i]),
            }
        )
    return words


# ---------------------------------------------------------------------------
# 6.5 — fuzzy-match Claude values to OCR bboxes; header_height_ratio (FR-040)
# ---------------------------------------------------------------------------


def fuzzy_match_bbox(value: str, ocr_words: list[dict], threshold: float = 0.7) -> dict | None:
    """Find the contiguous run of OCR words whose text best matches `value`.

    Returns the bounding box (top-left origin, pixels) covering that run, or
    `None` if no run scores at least `threshold` (`SequenceMatcher` ratio).
    """
    if not value or not ocr_words:
        return None

    target = _normalize_for_comparison(value)
    target_words = target.split()
    if not target_words:
        return None

    ordered = sorted(ocr_words, key=lambda w: (w["y"], w["x"]))
    best_ratio = 0.0
    best_box: dict | None = None

    max_window = min(len(target_words) + 2, len(ordered))
    for start in range(len(ordered)):
        for length in range(1, max_window - start + 1 if max_window - start > 0 else 0):
            window = ordered[start : start + length]
            if not window:
                continue
            candidate = _normalize_for_comparison(" ".join(w["text"] for w in window))
            ratio = SequenceMatcher(None, candidate, target).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                xs = [w["x"] for w in window]
                ys = [w["y"] for w in window]
                x2s = [w["x"] + w["w"] for w in window]
                y2s = [w["y"] + w["h"] for w in window]
                best_box = {"x": min(xs), "y": min(ys), "w": max(x2s) - min(xs), "h": max(y2s) - min(ys)}

    if best_ratio >= threshold:
        return best_box
    return None


def compute_header_height_ratio(ocr_words: list[dict], header_text: str = "GOVERNMENT WARNING") -> float | None:
    """Ratio of the "GOVERNMENT WARNING:" header's OCR text height to the median
    height of the surrounding body text (FR-040, corroborates FR-035).

    `None` if OCR found no words, or could not isolate the header text.
    """
    if not ocr_words:
        return None

    header_box = fuzzy_match_bbox(header_text, ocr_words, threshold=0.6)
    if header_box is None or header_box["h"] <= 0:
        return None

    header_height = header_box["h"]
    body_heights = [
        w["h"]
        for w in ocr_words
        if w["h"] > 0
        and not (
            header_box["x"] <= w["x"] < header_box["x"] + header_box["w"]
            and header_box["y"] <= w["y"] < header_box["y"] + header_box["h"]
        )
    ]
    if not body_heights:
        return None

    body_heights.sort()
    body_height = body_heights[len(body_heights) // 2]
    if body_height <= 0:
        return None

    return round(header_height / body_height, 3)


# ---------------------------------------------------------------------------
# 6.6 — Per-image concurrent execution (IA-19/IA-24)
# ---------------------------------------------------------------------------


async def _process_label_image(label_image: LabelImage, *, client: Anthropic | None) -> dict[str, list[LabelFieldResult]]:
    raw_bytes = await asyncio.to_thread(Path(label_image.image_path).read_bytes)
    preprocessed = await asyncio.to_thread(preprocess_image, raw_bytes)

    field_results, ocr_words = await asyncio.gather(
        asyncio.to_thread(extract_label_fields, preprocessed, client=client),
        asyncio.to_thread(run_ocr, preprocessed),
    )

    for field_name, results in field_results.items():
        for fr in results:
            if field_name == "government_warning":
                text = fr.value.get("text_found") if isinstance(fr.value, dict) else None
            else:
                text = fr.value if isinstance(fr.value, str) else None

            if text and ocr_words:
                fr.bbox = fuzzy_match_bbox(text, ocr_words)

            if field_name == "government_warning" and ocr_words:
                fr.header_height_ratio = compute_header_height_ratio(ocr_words)

    return field_results


async def run_stage4_extraction(
    label_images: list[LabelImage], *, client: Anthropic | None = None
) -> dict[int, dict[str, list[LabelFieldResult]]]:
    """Run Stage 4 for every label image concurrently (`asyncio.gather`, IA-19/IA-24)."""
    results = await asyncio.gather(*[_process_label_image(li, client=client) for li in label_images])
    return {label_image.id: result for label_image, result in zip(label_images, results)}


# ---------------------------------------------------------------------------
# 6.7 — Persistence (FR-038, DevLog §3.4)
# ---------------------------------------------------------------------------


def persist_label_parameters(
    db: Session, application: Application, results_by_image: dict[int, dict[str, list[LabelFieldResult]]]
) -> None:
    """Replace `label_parameters` rows for `application` — one row per (label_image_id, field_name)."""
    db.query(LabelParameter).filter(LabelParameter.application_id == application.id).delete()

    for label_image_id, field_results in results_by_image.items():
        for field_name, results in field_results.items():
            for fr in results:
                value = fr.value
                if isinstance(value, (list, dict)):
                    field_value: str | None = json.dumps(value)
                elif isinstance(value, bool):
                    field_value = "true" if value else "false"
                elif value is None:
                    field_value = None
                else:
                    field_value = str(value)

                db.add(
                    LabelParameter(
                        application_id=application.id,
                        label_image_id=label_image_id,
                        field_name=field_name,
                        field_value=field_value,
                        confidence=fr.confidence,
                        location_hint=fr.location_hint,
                        bbox_json=json.dumps(fr.bbox) if fr.bbox else None,
                        header_height_ratio=fr.header_height_ratio,
                    )
                )

    application.status = "LABEL_ASSESSED"
    db.commit()
    db.refresh(application)

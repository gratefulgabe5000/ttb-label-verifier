"""Stage 3: Form Assessment — tiered extraction of TTB Form F 5100.31 Part I (TS-01).

Tier 1 (pypdf AcroForm) -> Tier 2 (pdfplumber text layer) -> Tier 3 (Claude Vision).
Each field is resolved by the first tier that returns a non-empty value; any
field left unresolved after all three tiers keeps `extraction_method=None` and
`confidence=None` with a `location_hint` describing where to look on the form.

Field-name/coordinate mappings below (FIELD_NAME_MAP, FIELD_RECTS, checkbox
export values) are specific to TTB Form F 5100.31 (04/2023), per A-13 — future
form revisions rely on the Tier 3 vision fallback.
"""

from __future__ import annotations

import base64
import difflib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber
import pypdfium2
from anthropic import Anthropic
from pypdf import PdfReader
from sqlalchemy.orm import Session

from models.application import Application
from models.form_parameter import FormParameter
from services import settings_service

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical Stage 3 output fields (DevLog §3.2).
PART_I_FIELDS = [
    "representative_id",
    "plant_registry_number",
    "source",
    "serial_number",
    "product_type",
    "brand_name",
    "fanciful_name",
    "applicant_name",
    "applicant_address",
    "mailing_address",
    "formula_id",
    "grape_varietals",
    "wine_appellation",
    "phone_number",
    "email_address",
    "application_type",
    "embossed_info",
    "foreign_translations",
    "date_of_application",
    "signature_present",
    "applicant_printed_name",
]

# Page geometry for F 5100.31 (04/2023), in PDF points (bottom-left origin).
PAGE_HEIGHT = 1008.0

# Tier 1: canonical field -> exact AcroForm `/T` fully-qualified field name.
FIELD_NAME_MAP = {
    "representative_id": "1. REP. ID. NO. (If any)",
    "plant_registry_number": "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)",
    "brand_name": "6. BRAND NAME (Required)",
    "fanciful_name": "7. FANCIFUL NAME (If any)",
    "applicant_name_address": "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC",
    "mailing_address": "8a. MAILING ADDRESS, IF DIFFERENT",
    "formula_id": "9.  FORMULA",
    "grape_varietals": "10. GRAPE VARIETAL(S) Wine only",
    "wine_appellation": "11.  WINE APPELLATION (If on label)",
    "phone_number": "12.  PHONE NUMBER",
    "email_address": "13.  EMAIL ADDRESS",
    "embossed_info": (
        "15.  SHOW ANY INFORMATION THAT IS BLOWN, BRANDED, OR EMBOSSED ON THE "
        "CONTAINER (e.g., net contents) ONLY IF IT DOES NOT APPEAR ON THE LABELS"
    ),
    "date_of_application": "16.  DATE OF APPLICATION",
    "applicant_printed_name": "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT",
}

# Tier 1/2/3 bounding boxes (PDF rect, bottom-left origin: x0, y0, x1, y1).
FIELD_RECTS: dict[str, tuple[float, float, float, float]] = {
    "representative_id": (22.9, 909.4, 135.2, 923.8),
    "plant_registry_number": (19.7, 859.6, 134.1, 883.9),
    "source": (140.4, 871.2, 208.0, 880.1),
    "serial_number": (19.7, 803.0, 138.6, 831.6),
    "product_type": (146.6, 806.1, 157.2, 838.3),
    "brand_name": (21.9, 778.9, 246.1, 794.6),
    "fanciful_name": (21.9, 754.1, 246.1, 769.9),
    "applicant_name_address": (251.9, 810.8, 591.2, 868.1),
    "mailing_address": (251.9, 754.9, 591.2, 800.2),
    "formula_id": (21.9, 721.1, 141.9, 744.4),
    "grape_varietals": (144.4, 721.5, 387.0, 743.9),
    "wine_appellation": (21.5, 687.4, 385.9, 709.1),
    "phone_number": (20.6, 654.0, 145.9, 673.5),
    "email_address": (147.9, 654.0, 386.6, 673.5),
    "application_type": (397.0, 658.2, 593.0, 740.9),
    "embossed_info": (21.9, 584.7, 592.4, 636.0),
    "date_of_application": (21.9, 495.7, 120.4, 518.2),
    "applicant_printed_name": (352.9, 496.0, 590.0, 516.7),
}

# Item 3 (Source) checkbox export values.
SOURCE_FIELD = "Check Box34"

# Item 5 (Type of Product) checkbox export values.
PRODUCT_TYPE_FIELD = "Check Box22"

# Item 4 (Serial Number) AcroForm fields, in display order.
SERIAL_FIELDS = ["YEAR 1", "YEAR 2", "SERIAL NUMBER 1", "SERIAL NUMBER 2", "SERIAL NUMBER 3", "SERIAL NUMBER 4"]

# Item 14 (Application Type) AcroForm fields.
APPLICATION_TYPE_FIELDS = {
    "14a": "14a. CERTIFICATE OF LABEL APPROVAL",
    "14b": "14b. CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL",
    "14b_state": "14 b (Fill in State abbreviation)",
    "14c": "14c. DISTINCTIVE LIQUOR BOTTLE APPROVAL",
    "14c_capacity": "14c.  TOTAL BOTTLE CAPACITY BEFORE CLOSURE (Fill in amount)",
    "14d": "14d. RESUBMISSION AFTER REJECTION",
    "prior_ttb_id": "TTB ID",
}

# Tier 2 fields handled by the generic "largest font size in region" extractor.
# source/product_type/application_type/signature_present/foreign_translations
# are never attempted at Tier 2 — their regions either have no text-layer
# representation or are dominated by neighboring static label text.
TIER2_GENERIC_FIELDS = [
    "representative_id",
    "plant_registry_number",
    "brand_name",
    "fanciful_name",
    "applicant_name_address",
    "mailing_address",
    "formula_id",
    "grape_varietals",
    "wine_appellation",
    "phone_number",
    "email_address",
    "embossed_info",
    "date_of_application",
    "applicant_printed_name",
]

# Human-readable fallback locations for unresolved fields / Tier 3 results.
LOCATION_HINTS = {
    "representative_id": "Form Part I, Item 1 (Representative ID Number)",
    "plant_registry_number": "Form Part I, Item 2 (Plant Registry/Basic Permit/Brewer's Number)",
    "source": "Form Part I, Item 3 (Source: Domestic or Imported)",
    "serial_number": "Form Part I, Item 4 (Serial Number)",
    "product_type": "Form Part I, Item 5 (Type of Product)",
    "brand_name": "Form Part I, Item 6 (Brand Name)",
    "fanciful_name": "Form Part I, Item 7 (Fanciful Name)",
    "applicant_name": "Form Part I, Item 8 (Applicant Name)",
    "applicant_address": "Form Part I, Item 8 (Applicant Address)",
    "mailing_address": "Form Part I, Item 8a (Mailing Address, if different)",
    "formula_id": "Form Part I, Item 9 (Formula)",
    "grape_varietals": "Form Part I, Item 10 (Grape Varietal(s), wine only)",
    "wine_appellation": "Form Part I, Item 11 (Wine Appellation)",
    "phone_number": "Form Part I, Item 12 (Phone Number)",
    "email_address": "Form Part I, Item 13 (Email Address)",
    "application_type": "Form Part I, Item 14 (Application Type: a-d)",
    "embossed_info": "Form Part I, Item 15 (Embossed/Blown Container Info; foreign language translations)",
    "foreign_translations": "Form Part I, Item 15 (Foreign Language Translations)",
    "date_of_application": "Form Part I, Item 16 (Date of Application)",
    "signature_present": "Form Part I, Item 17 (Signature)",
    "applicant_printed_name": "Form Part I, Item 18 (Printed Name of Applicant or Authorized Agent)",
}

# Static system prompt for Tier 3 (Claude Vision) — kept identical across
# calls so it can be marked with `cache_control` for prompt caching (IA-25).
STAGE3_SYSTEM_PROMPT = """You are a data-extraction assistant for the Alcohol and Tobacco Tax and \
Trade Bureau (TTB). You will be shown an image of Part I of TTB Form 5100.31 \
("Application for and Certification/Exemption of Label/Bottle Approval").

Read the form image carefully and extract the requested fields. Respond with \
ONLY a single JSON object (no markdown fences, no commentary) with this shape:

{
  "values": {
    "representative_id": "<string or null>",
    "plant_registry_number": "<string or null>",
    "source": "<'domestic' | 'imported' | null>",
    "serial_number": "<string or null, formatted as 'YY-N'>",
    "product_type": "<'wine' | 'distilled_spirits' | 'malt_beverages' | null>",
    "brand_name": "<string or null>",
    "fanciful_name": "<string or null>",
    "applicant_name": "<string or null>",
    "applicant_address": "<string or null>",
    "mailing_address": "<string or null>",
    "formula_id": "<string or null>",
    "grape_varietals": "<array of strings or null>",
    "wine_appellation": "<string or null>",
    "phone_number": "<string or null>",
    "email_address": "<string or null>",
    "application_type": {
      "checked": "<array, subset of ['14a','14b','14c','14d']>",
      "exemption_state": "<string or null>",
      "container_capacity": "<string or null>",
      "prior_ttb_id": "<string or null>"
    },
    "embossed_info": "<string or null>",
    "foreign_translations": "<string or null>",
    "date_of_application": "<string or null>",
    "signature_present": "<true | false>",
    "applicant_printed_name": "<string or null>"
  },
  "confidence_scores": {
    "<field name>": "<float 0.0-1.0, your confidence in that field's value>"
  }
}

Only include keys for the fields you were asked to extract. Use null for any \
field that is blank, illegible, or not present on the form. Do not guess at \
values that are not visible on the form."""


@dataclass
class FieldResult:
    """One field's extraction result, ready for `persist_form_parameters`."""

    value: Any
    confidence: float | None
    extraction_method: str | None  # "acroform" | "pdftext" | "ai_vision" | None
    bbox: dict | None
    location_hint: str | None = None


# ---------------------------------------------------------------------------
# Normalization helpers (5.4)
# ---------------------------------------------------------------------------


def normalize_source(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip().lstrip("/").lower()
    if raw.startswith("domes"):
        return "domestic"
    if raw.startswith("import"):
        return "imported"
    return None


def normalize_product_type(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip().lstrip("/").lower()
    if raw.startswith("wine"):
        return "wine"
    if raw.startswith("spirit"):
        return "distilled_spirits"
    if raw.startswith("malt"):
        return "malt_beverages"
    return None


def normalize_serial_number(raw: str | None) -> str | None:
    """"260001" -> "26-1" (2-digit year, sequence number with leading zeros stripped)."""
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if len(digits) < 3:
        return (raw or "").strip() or None
    year, seq = digits[:2], digits[2:]
    return f"{year}-{int(seq)}"


def normalize_grape_varietals(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    parts = re.split(r"[,;\n]+", raw)
    result = [p.strip() for p in parts if p.strip()]
    return result or None


def _split_name_address(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None, None
    name = lines[0]
    address = "\n".join(lines[1:]) or None
    return name, address


# ---------------------------------------------------------------------------
# bbox helpers
# ---------------------------------------------------------------------------


def _rect_to_bbox(rect: tuple[float, float, float, float], page_height: float) -> dict:
    """Convert a PDF rect (bottom-left origin) to a top-left-origin bbox."""
    x0, y0, x1, y1 = rect
    return {
        "page": 0,
        "x": round(x0, 1),
        "y": round(page_height - y1, 1),
        "w": round(x1 - x0, 1),
        "h": round(y1 - y0, 1),
    }


def _chars_to_bbox(chars: list[dict]) -> dict:
    """Bounding box (top-left origin) covering a list of pdfplumber chars."""
    x0 = min(c["x0"] for c in chars)
    x1 = max(c["x1"] for c in chars)
    top = min(c["top"] for c in chars)
    bottom = max(c["bottom"] for c in chars)
    return {
        "page": 0,
        "x": round(x0, 1),
        "y": round(top, 1),
        "w": round(x1 - x0, 1),
        "h": round(bottom - top, 1),
    }


# ---------------------------------------------------------------------------
# Tier 1: pypdf AcroForm (FR-010-019, IA-23)
# ---------------------------------------------------------------------------


def extract_tier1(pdf_path: str | Path) -> dict[str, FieldResult]:
    """Read AcroForm field values directly. <10ms, $0, confidence 1.0."""
    results: dict[str, FieldResult] = {}

    try:
        reader = PdfReader(pdf_path)
        fields = reader.get_fields()
    except Exception:
        return results

    if not fields:
        return results

    def field_value(name: str) -> str | None:
        field = fields.get(name)
        if field is None or field.value is None:
            return None
        value = str(field.value).strip()
        return value or None

    for canonical, acro_name in FIELD_NAME_MAP.items():
        if canonical == "applicant_name_address":
            continue
        raw = field_value(acro_name)
        if raw is None:
            continue
        value: Any = normalize_grape_varietals(raw) if canonical == "grape_varietals" else raw
        bbox = _rect_to_bbox(FIELD_RECTS[canonical], PAGE_HEIGHT)
        results[canonical] = FieldResult(value, 1.0, "acroform", bbox)

    # Item 8 — applicant name + address (single AcroForm field, split).
    raw_8 = field_value(FIELD_NAME_MAP["applicant_name_address"])
    if raw_8 is not None:
        name, address = _split_name_address(raw_8)
        bbox = _rect_to_bbox(FIELD_RECTS["applicant_name_address"], PAGE_HEIGHT)
        if name:
            results["applicant_name"] = FieldResult(name, 1.0, "acroform", bbox)
        if address:
            results["applicant_address"] = FieldResult(address, 1.0, "acroform", bbox)

    # Item 3 — source (checkbox).
    raw_source = field_value(SOURCE_FIELD)
    source = normalize_source(raw_source) if raw_source and raw_source != "/Off" else None
    if source:
        results["source"] = FieldResult(source, 1.0, "acroform", _rect_to_bbox(FIELD_RECTS["source"], PAGE_HEIGHT))

    # Item 5 — product type (checkbox group).
    raw_product = field_value(PRODUCT_TYPE_FIELD)
    product_type = normalize_product_type(raw_product) if raw_product and raw_product != "/Off" else None
    if product_type:
        results["product_type"] = FieldResult(
            product_type, 1.0, "acroform", _rect_to_bbox(FIELD_RECTS["product_type"], PAGE_HEIGHT)
        )

    # Item 4 — serial number (YEAR 1/2 + SERIAL NUMBER 1-4 concatenated).
    digits = "".join(field_value(name) or "" for name in SERIAL_FIELDS)
    serial_number = normalize_serial_number(digits) if digits else None
    if serial_number:
        results["serial_number"] = FieldResult(
            serial_number, 1.0, "acroform", _rect_to_bbox(FIELD_RECTS["serial_number"], PAGE_HEIGHT)
        )

    # Item 14 — application type (14a-d checkboxes + sub-fields).
    checked = [
        key
        for key in ("14a", "14b", "14c", "14d")
        if (raw := field_value(APPLICATION_TYPE_FIELDS[key])) and raw != "/Off"
    ]
    if checked:
        app_type = {
            "checked": checked,
            "exemption_state": field_value(APPLICATION_TYPE_FIELDS["14b_state"]),
            "container_capacity": field_value(APPLICATION_TYPE_FIELDS["14c_capacity"]),
            "prior_ttb_id": field_value(APPLICATION_TYPE_FIELDS["prior_ttb_id"]),
        }
        results["application_type"] = FieldResult(
            app_type, 1.0, "acroform", _rect_to_bbox(FIELD_RECTS["application_type"], PAGE_HEIGHT)
        )

    return results


# ---------------------------------------------------------------------------
# Tier 2: pdfplumber text layer (FR-010-019, IA-23)
# ---------------------------------------------------------------------------


def _crop_region(page, rect: tuple[float, float, float, float], page_height: float, pad: float = 1.0):
    x0, y0, x1, y1 = rect
    bbox = (
        max(x0 - pad, 0),
        max(page_height - y1 - pad, 0),
        min(x1 + pad, page.width),
        min(page_height - y0 + pad, page_height),
    )
    return page.crop(bbox)


def _filter_value_chars(chars: list[dict]) -> list[dict]:
    """Keep only the largest-font-size chars in a region.

    Static form labels render at a smaller font size than baked-in filled
    values, even when their bounding boxes overlap — this filter separates
    the value text from the label text without any garble-detection logic.
    """
    if not chars:
        return []
    max_size = max(c["size"] for c in chars)
    return [c for c in chars if c["size"] >= max_size - 0.5]


def _chars_to_text(chars: list[dict]) -> str | None:
    if not chars:
        return None
    lines: dict[float, list[dict]] = {}
    for c in chars:
        key = round(c["top"], 0)
        lines.setdefault(key, []).append(c)
    out_lines = []
    for key in sorted(lines.keys()):
        line_chars = sorted(lines[key], key=lambda c: c["x0"])
        out_lines.append("".join(c["text"] for c in line_chars))
    text = "\n".join(out_lines).strip()
    return text or None


def _is_label_text(value: str, label: str) -> bool:
    """True if `value` is just the field's own static label (empty field)."""
    if not label:
        return False
    normalized = lambda s: " ".join(s.upper().split())
    ratio = difflib.SequenceMatcher(None, normalized(value), normalized(label)).ratio()
    return ratio > 0.8


def extract_tier2(pdf_path: str | Path) -> dict[str, FieldResult]:
    """Read filled-in text directly from the PDF text layer. <200ms, $0, confidence ~0.92."""
    results: dict[str, FieldResult] = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return results
            page = pdf.pages[0]
            page_height = page.height

            for canonical in TIER2_GENERIC_FIELDS:
                crop = _crop_region(page, FIELD_RECTS[canonical], page_height)
                value_chars = _filter_value_chars(crop.chars)
                value_text = _chars_to_text(value_chars)
                if value_text is None:
                    continue
                if _is_label_text(value_text, FIELD_NAME_MAP.get(canonical, "")):
                    continue
                bbox = _chars_to_bbox(value_chars)

                if canonical == "applicant_name_address":
                    name, address = _split_name_address(value_text)
                    if name:
                        results["applicant_name"] = FieldResult(name, 0.92, "pdftext", bbox)
                    if address:
                        results["applicant_address"] = FieldResult(address, 0.92, "pdftext", bbox)
                elif canonical == "grape_varietals":
                    results[canonical] = FieldResult(normalize_grape_varietals(value_text), 0.92, "pdftext", bbox)
                else:
                    results[canonical] = FieldResult(value_text, 0.92, "pdftext", bbox)

            # Item 4 — serial number: only the digit characters are at the
            # baked-in font size; decoration ("-") is at the largest size.
            crop = _crop_region(page, FIELD_RECTS["serial_number"], page_height)
            digit_chars = sorted((c for c in crop.chars if c["text"].isdigit()), key=lambda c: c["x0"])
            if digit_chars:
                digits = "".join(c["text"] for c in digit_chars)
                serial_number = normalize_serial_number(digits)
                if serial_number:
                    results["serial_number"] = FieldResult(serial_number, 0.92, "pdftext", _chars_to_bbox(digit_chars))
    except Exception:
        return results

    return results


# ---------------------------------------------------------------------------
# Tier 3: Claude Vision fallback (FR-010-016, IA-23, IA-25)
# ---------------------------------------------------------------------------


def _render_first_page_png(pdf_path: str | Path, scale: float = 2.0) -> bytes:
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    try:
        image = pdf[0].render(scale=scale).to_pil()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    finally:
        pdf.close()


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


def extract_tier3(pdf_path: str | Path, needed_fields: list[str], *, client: Anthropic | None = None) -> dict[str, FieldResult]:
    """Render page 1 and ask Claude Vision for the still-missing fields.

    Returns `{}` (Tier 1/2 results still persist) if no API key is configured
    (IA-02) or if the call fails for any reason.
    """
    if not needed_fields:
        return {}

    if client is None:
        if not settings_service.is_configured():
            return {}
        client = Anthropic()

    try:
        image_bytes = _render_first_page_png(pdf_path)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[{"type": "text", "text": STAGE3_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
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
                            "text": (
                                "Extract these fields from this TTB Form F 5100.31 application as JSON: "
                                + ", ".join(needed_fields)
                            ),
                        },
                    ],
                }
            ],
        )
        data = _parse_json_response(response.content[0].text)
    except Exception:
        return {}

    values = data.get("values", {}) if isinstance(data, dict) else {}
    confidences = data.get("confidence_scores", {}) if isinstance(data, dict) else {}

    results: dict[str, FieldResult] = {}
    for field in needed_fields:
        if field not in values:
            continue
        value = values[field]
        if value in (None, "", []):
            continue
        confidence = confidences.get(field, 0.75)
        results[field] = FieldResult(value, confidence, "ai_vision", None, LOCATION_HINTS.get(field))

    return results


# ---------------------------------------------------------------------------
# Orchestration (DevLog §3.2)
# ---------------------------------------------------------------------------


def run_stage3_extraction(pdf_path: str | Path, *, client: Anthropic | None = None) -> dict[str, FieldResult]:
    """Run Tier 1 -> Tier 2 -> Tier 3, first non-empty value per field wins."""
    results: dict[str, FieldResult] = {}

    for field, fr in extract_tier1(pdf_path).items():
        if fr.value not in (None, "", []):
            results[field] = fr

    for field, fr in extract_tier2(pdf_path).items():
        if field not in results and fr.value not in (None, "", []):
            results[field] = fr

    missing = [f for f in PART_I_FIELDS if f not in results]
    if missing:
        for field, fr in extract_tier3(pdf_path, missing, client=client).items():
            if field not in results:
                results[field] = fr

    for field in PART_I_FIELDS:
        if field not in results:
            results[field] = FieldResult(None, None, None, None, LOCATION_HINTS.get(field))

    return results


# ---------------------------------------------------------------------------
# Persistence (DevLog §3.4)
# ---------------------------------------------------------------------------


def _next_ttb_id(db: Session) -> str:
    """Auto-assign a 14-digit TTB ID for an application that arrives without
    one. Digits 1-2 are the 2-digit submission year, 3-5 the Julian day of
    the year, 6-8 the submission method (always "001" -- e-filed -- for
    system-assigned IDs), and 9-14 a sequence that resets to 000001 each day
    for each method code."""
    now = datetime.now()
    prefix = f"{now:%y}{now:%j}001"

    existing = db.query(Application.ttb_id).filter(Application.ttb_id.like(f"{prefix}%")).all()
    max_sequence = max((int(ttb_id[8:]) for (ttb_id,) in existing if ttb_id and len(ttb_id) == 14), default=0)

    return f"{prefix}{max_sequence + 1:06d}"


def persist_form_parameters(db: Session, application: Application, results: dict[str, FieldResult]) -> None:
    """Replace `form_parameters` rows for `application` and update its denormalized columns."""
    db.query(FormParameter).filter(FormParameter.application_id == application.id).delete()

    for field_name, fr in results.items():
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
            FormParameter(
                application_id=application.id,
                field_name=field_name,
                field_value=field_value,
                confidence=fr.confidence,
                extraction_method=fr.extraction_method,
                location_hint=fr.location_hint,
                bbox_json=json.dumps(fr.bbox) if fr.bbox else None,
            )
        )

    permit_no = results["plant_registry_number"].value
    if permit_no:
        application.permit_no = permit_no

    brand_name = results["brand_name"].value
    if brand_name:
        application.brand_name = brand_name

    fanciful_name = results["fanciful_name"].value
    if fanciful_name:
        application.fanciful_name = fanciful_name

    applicant_name = results["applicant_name"].value
    if applicant_name:
        application.applicant_name = applicant_name

    product_type = results["product_type"].value
    if product_type:
        application.product_type = product_type

    source = results["source"].value
    if source:
        application.source = source

    serial_number = results["serial_number"].value
    if serial_number:
        application.serial_number = serial_number
        application.year = serial_number.split("-")[0]

    app_type = results["application_type"].value
    if app_type:
        if app_type.get("checked"):
            application.application_type = app_type["checked"][0]
        prior_ttb_id = app_type.get("prior_ttb_id")
        if prior_ttb_id:
            application.ttb_id = prior_ttb_id

    if not application.ttb_id:
        application.ttb_id = _next_ttb_id(db)

    application.status = "FORM_ASSESSED"
    db.commit()
    db.refresh(application)

"""
WBS 2.7 -- Type 14b ("for sale in one state only") application + matching
label set, per FR-056.

FR-056: "The system SHALL verify that at least one of the application's
label images contains 'For sale in [STATE] only' when Form Item 14b is
checked, using the state abbreviation declared in Item 14b. | Test: process
14b application with the correct statement on any one label image; confirm
MATCH. With the statement on no image; confirm HARD_FAILURE."

The "no statement -> HARD_FAILURE" half of FR-056 is already covered by the
WBS 2.4 fixture `hf_14b_woodford` (Item 14b checked for Ohio, no
"FOR SALE IN OHIO ONLY" statement on any of the three submitted Woodford
Reserve label images). This script builds the other half: a Type 14b
application where the matching state-restriction statement IS present on a
submitted label image, so the Type 14b row resolves to MATCH (not
HARD_FAILURE/NOT_APPLICABLE) and the overall outcome is APPROVE.

Real label images rarely carry a printed "For sale in [STATE] only"
statement -- it's added as a separate small statement label/sticker for
products sold under a state-restricted Certificate of Exemption from Label
Approval (27 CFR 13). No such image exists in testdata/, so this script
generates one with Pillow: a small statement-label mockup reading
"FOR SALE IN PENNSYLVANIA ONLY", saved to testdata/synthetic/ (clearly
separated from the real photographed label images in manifest.json).

Pairs with the EXISTING real "Stoll & Wolfe" whiskey label images
(domestic American Straight Whiskey blend, "Bottled by Heritage Spirits LLC
- Lancaster, PA"), an unused product from manifest.json (WBS 2.1) -- chosen
over yet another Woodford Reserve fixture for corpus diversity, and because
its real-world Lancaster, PA bottler gives a natural state for the
synthetic "FOR SALE IN PENNSYLVANIA ONLY" statement.

Outputs:
  synthetic/stollwolfe_for_sale_pa.jpg   synthetic state-restriction label
  forms/type14b_match_stollwolfe.pdf     AcroForm-filled F 5100.31, 14b/PA

See testdata/test_sets.json for the per-field comparison expectations and
label image references.

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_type14b_sets.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_good_sets import _COMMON
from formlib import OUT_DIR, fill_form

ROOT = Path(__file__).resolve().parent
SYNTHETIC_DIR = ROOT / "synthetic"

STATE_NAME = "PENNSYLVANIA"
STATE_ABBR = "PA"

# ---------------------------------------------------------------------------
# Type 14b application: "Stoll & Wolfe" American Straight Whiskey blend
# (domestic, distilled spirits -- 14b-eligible per the Item 14 reference
# table). All fields match the existing real label images
# ("Stoll & Wolfe whiskey front.jpg" / "...back.jpg") except Item 14, which
# is switched from 14a to 14b/PA to exercise FR-056's MATCH path against the
# synthetic state-restriction label below.
# ---------------------------------------------------------------------------
TYPE14B_MATCH_STOLLWOLFE = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "DSP-PA-19",
    "Check Box34": "/Domes",  # Item 3: Source of Product -- Domestic
    "Check Box22": "/Spirits",  # Item 5: Type of Product -- Distilled Spirits
    "6. BRAND NAME (Required)": "Stoll & Wolfe",
    "7. FANCIFUL NAME (If any)": "",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Heritage Spirits LLC\n450 Distillery Lane\nLancaster, PA 17602"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(717) 555-0142",
    "13.  EMAIL ADDRESS": "compliance@stollandwolfedistillery.com",
    "14a. CERTIFICATE OF LABEL APPROVAL": "/Off",
    "14b. CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL": "/yes",
    "14 b (Fill in State abbreviation)": STATE_ABBR,
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Avery J. Hahn",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "9",
}


def build_state_restriction_label(output_path: Path) -> None:
    """Generate a small statement-label mockup reading
    'FOR SALE IN PENNSYLVANIA ONLY' (FR-056), styled as a separate sticker
    rather than part of the front/back label artwork."""
    width, height = 700, 180
    img = Image.new("RGB", (width, height), (245, 240, 230))
    draw = ImageDraw.Draw(img)

    border_color = (60, 40, 20)
    draw.rectangle((4, 4, width - 5, height - 5), outline=border_color, width=4)

    header_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    body_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)

    header_text = "CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL"
    body_text = f"FOR SALE IN {STATE_NAME} ONLY"

    for text, font, y in (
        (header_text, header_font, 45),
        (body_text, body_font, 95),
    ):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w) / 2, y), text, font=font, fill=border_color)

    img.save(output_path, quality=90)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    label_path = SYNTHETIC_DIR / "stollwolfe_for_sale_pa.jpg"
    build_state_restriction_label(label_path)
    print(f"Wrote {label_path}")

    form_path = OUT_DIR / "type14b_match_stollwolfe.pdf"
    fill_form(TYPE14B_MATCH_STOLLWOLFE, form_path)
    print(f"Wrote {form_path}")


if __name__ == "__main__":
    main()

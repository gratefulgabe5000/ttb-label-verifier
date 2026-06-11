"""
WBS 2.2 -- Synthetic F 5100.31 sample form generator (TS-01 / FR-017).

Generates one fictional "Sample Creek Distillery" COLA application as three
PDF variants, one per extraction tier exercised by the Stage 3 form
extractor:

  *_acroform.pdf   Tier 1 -- filled AcroForm (pypdf field read)
  *_flattened.pdf  Tier 2 -- AcroForm removed, values drawn into a text layer
                              (pdfplumber text extraction)
  *_scanned.pdf    Tier 3 -- rasterized page image, no extractable text
                              (Claude Vision fallback)

Source template: ../_ProblemStatement/f510031.pdf (official TTB Form
F 5100.31, 04/2023, AES-encrypted with an empty user password).

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_sample_forms.py
"""

from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parent / "_ProblemStatement" / "f510031.pdf"
OUT_DIR = ROOT / "forms"

# Fully-qualified AcroForm field names (pypdf get_fields() keys) -> values
# for the fictional "Sample Creek Distillery" domestic straight bourbon
# whiskey COLA application. Field names/states reverse-engineered from
# f510031.pdf's AcroForm dictionary (WBS 2.2).
SAMPLE_VALUES = {
    "1. REP. ID. NO. (If any)": "",
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "DSP-GA-20123",
    "Check Box34": "/Domes",  # Item 3: Source of Product -- Domestic
    "6. BRAND NAME (Required)": "Sample Creek",
    "7. FANCIFUL NAME (If any)": "Heritage Reserve",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Sample Creek Distillery, LLC\n123 Distillery Lane\nWarner Robins, GA 31088"
    ),
    "8a. MAILING ADDRESS, IF DIFFERENT": "",
    "Check Box22": "/Spirits",  # Item 5: Type of Product -- Distilled Spirits
    "9.  FORMULA": "",
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(478) 555-0142",
    "13.  EMAIL ADDRESS": "compliance@samplecreekdistillery.com",
    "14a. CERTIFICATE OF LABEL APPROVAL": "/yes",
    "14b. CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL": "/Off",
    "14 b (Fill in State abbreviation)": "",
    "14c. DISTINCTIVE LIQUOR BOTTLE APPROVAL": "/Off",
    "14c.  TOTAL BOTTLE CAPACITY BEFORE CLOSURE (Fill in amount)": "",
    "14d. RESUBMISSION AFTER REJECTION": "/Off",
    "15.  SHOW ANY INFORMATION THAT IS BLOWN, BRANDED, OR EMBOSSED ON THE CONTAINER (e.g., net contents) ONLY IF IT DOES NOT APPEAR ON THE LABELS": (
        "NET CONTENTS 750 ML BLOWN INTO BASE OF BOTTLE"
    ),
    "16.  DATE OF APPLICATION": "06/01/2026",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Jordan T. Avery",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "1",
    "TTB ID": "",
}

def fill_form(output_path: Path) -> None:
    """Tier 1: write a copy of the template with AcroForm fields populated."""
    reader = PdfReader(TEMPLATE)
    reader.decrypt("")

    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, SAMPLE_VALUES, auto_regenerate=False)

    with open(output_path, "wb") as f:
        writer.write(f)


def flatten_form(acroform_path: Path, output_path: Path) -> None:
    """Tier 2: bake the filled widgets' appearances into permanent page
    content and remove the AcroForm, leaving a plain text/vector layer."""
    doc = fitz.open(acroform_path)
    doc.bake(annots=False, widgets=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def rasterize_to_image_pdf(flattened_path: Path, output_path: Path, dpi: int = 150) -> None:
    """Tier 3: render each page to a raster image and rebuild a PDF
    containing only those images (no extractable text)."""
    src = fitz.open(flattened_path)
    out = fitz.open()

    for page in src:
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")

        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)

    out.save(output_path)
    out.close()
    src.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    acroform_path = OUT_DIR / "sample_creek_acroform.pdf"
    flattened_path = OUT_DIR / "sample_creek_flattened.pdf"
    scanned_path = OUT_DIR / "sample_creek_scanned.pdf"

    fill_form(acroform_path)
    print(f"Wrote {acroform_path}")

    flatten_form(acroform_path, flattened_path)
    print(f"Wrote {flattened_path}")

    rasterize_to_image_pdf(flattened_path, scanned_path)
    print(f"Wrote {scanned_path}")


if __name__ == "__main__":
    main()

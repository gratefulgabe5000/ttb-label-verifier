"""
Shared helpers for generating synthetic F 5100.31 fixtures (TS-01 / FR-017).

Used by build_sample_forms.py (WBS 2.2 -- tiered extraction fixtures) and
build_good_sets.py (WBS 2.3 -- comparison-engine "good" sets), and any
later WBS 2.4-2.7 fixture builders.

Source template: ../_ProblemStatement/f510031.pdf (official TTB Form
F 5100.31, 04/2023, AES-encrypted with an empty user password).
"""

from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parent / "_ProblemStatement" / "f510031.pdf"
OUT_DIR = ROOT / "forms"


def fill_form(field_values: dict, output_path: Path) -> None:
    """Write a copy of the template with the given AcroForm fields populated.

    field_values keys are fully-qualified field names as returned by
    pypdf's PdfReader.get_fields(); values are the desired /V entries
    (strings for text fields, "/<ExportState>" or "/Off" for
    checkboxes/radio buttons).
    """
    reader = PdfReader(TEMPLATE)
    reader.decrypt("")

    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values, auto_regenerate=False)

    with open(output_path, "wb") as f:
        writer.write(f)


def flatten_form(acroform_path: Path, output_path: Path) -> None:
    """Bake the filled widgets' appearances into permanent page content and
    remove the AcroForm, leaving a plain text/vector layer."""
    doc = fitz.open(acroform_path)
    doc.bake(annots=False, widgets=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def rasterize_to_image_pdf(flattened_path: Path, output_path: Path, dpi: int = 150) -> None:
    """Render each page to a raster image and rebuild a PDF containing only
    those images (no extractable text)."""
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

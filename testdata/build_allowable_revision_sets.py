"""
WBS 2.5 -- "Possible allowable revision" application + label sets, one per
named example in the WBS row (case/punctuation brand differences, in-state
address change), per Sec. 2.6 Allowable Revisions / FR-057, FR-059, FR-103.

Each set pairs a synthetic, filled-AcroForm F 5100.31 with an EXISTING real
label image group from testdata/ (cataloged in manifest.json, WBS 2.1). Each
fixture takes a WBS 2.3 "good" baseline and changes exactly ONE field so that
exactly one comparison rule resolves to POSSIBLE_ALLOWABLE (with a populated
Section V item reference, FR-059); every other rule remains MATCH/
NOT_APPLICABLE as in the baseline, so the expected pipeline outcome is
RECOMMEND EXEMPTION REVIEW (FR-062).

Rule -> fixture map:
  Brand Name case/punctuation/spacing (Sec. V 3b, FR-051/052/057)
      -> ar_brandname_fortemasso.pdf
  Applicant Address in-state street change (Sec. V 19, FR-103)
      -> ar_address_barrilito.pdf

Note on the WBS 2.5 row's third named example, "color/font differences"
(Sec. V 3a/3b -- also FR-057's literal test case, "only label colors
differ"): this describes a label-APPEARANCE attribute (color, typeface) with
no corresponding field on Form F 5100.31, so it cannot be expressed as a
form-value-vs-label-value comparison row in the test_sets.json schema used
here. See test_sets.json source_note and DevLog Sec. 2.5/2.6 outcome notes
for the documented scoping decision.

See testdata/test_sets.json for the per-field comparison expectations and
label image references for each set.

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_allowable_revision_sets.py
"""

from formlib import OUT_DIR, fill_form
from build_good_sets import _COMMON, MALT_BARRILITO

# ---------------------------------------------------------------------------
# Brand Name case/punctuation/spacing difference (Sec. V item 3b)
#
# Forte Masso (imported wine, Italy) -- corrected version of the WBS 2.4
# hf_producttype_fortemasso baseline, with Check Box22 = /Wine (matching the
# label's "BARBERA D'ALBA ... RED WINE" class/type designation -- the Item 5
# conflict from 2.4 is fixed here so that ONLY the Brand Name row is
# non-MATCH).
#
# Label images: "Forte Masso beer front.jpg" (wordmark "FORTEMASSO", one
# word, all-caps stylized lettering with decorative star-in-O glyphs) and
# "...beer back.jpg" ("FORTEMASSO 2013 BARBERA D'ALBA DENOMINAZIONE DI ORIGINE
# CONTROLLATA RED WINE ... IMPORTED BY: DUE FRATELLI IMPORTS, LLC PORTLAND
# MAINE ... 750 ML. ... PRODOTTO IN ITALIA PRODUCT OF ITALY ... 13,5% vol ...
# Government Warning).
#
# Form Item 6 = "Forte Masso" (two words, Title Case, per manifest.json's
# brand_name); the label wordmark reads "FORTEMASSO" (one word, all caps).
# The discrepancy is limited to spacing/word-division and case -- not a
# substantive difference in the brand's identity (FR-052) -- and corresponds
# to Sec. V item 3b ("change ... type size, font, spelling, case, or
# punctuation"), so the Brand Name comparison resolves to POSSIBLE_ALLOWABLE
# with section_v_ref "3b" (FR-057, FR-059).
# ---------------------------------------------------------------------------
AR_BRANDNAME_FORTEMASSO = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "IMP-ME-3307",
    "Check Box34": "/Import",
    "Check Box22": "/Wine",  # corrected: label is unambiguously wine (Barbera d'Alba DOCG)
    "6. BRAND NAME (Required)": "Forte Masso",
    "7. FANCIFUL NAME (If any)": "",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Due Fratelli Imports, LLC\n88 Marginal Way\nPortland, ME 04101"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "Barbera d'Alba",
    "12.  PHONE NUMBER": "(207) 555-0163",
    "13.  EMAIL ADDRESS": "compliance@duefratelliimports.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Lena M. Caruso",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "7",
}

# ---------------------------------------------------------------------------
# Applicant Address in-state street change (Sec. V item 19)
#
# Cerveza Barrilito (imported malt beverage, Mexico) -- WBS 2.3
# good_malt_barrilito baseline, with Item 8's STREET ADDRESS changed to a
# different street within the same city/state/ZIP as the label.
#
# Label image: "Cerveza Barrilito.jpg" -- "IMPORTED BY: RR IMPORTACIONES INC.
# 141 3RD ST, UNIT #143 PASSAIC, N.J. 07055-0000".
#
# Form Item 8 below reads "RR Importaciones Inc., 200 Brook Avenue, Passaic,
# NJ 07055" -- same importer name, same city/state/ZIP as the label, but a
# different street address. Per FR-103, an address mismatch limited to an
# in-state change is POSSIBLE_ALLOWABLE (Sec. V item 19, "Change ... address
# within same state"), not HARD_FAILURE.
# ---------------------------------------------------------------------------
AR_ADDRESS_BARRILITO = {
    **MALT_BARRILITO,
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "RR Importaciones Inc.\n200 Brook Avenue\nPassaic, NJ 07055"
    ),
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "8",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sets = {
        "ar_brandname_fortemasso.pdf": AR_BRANDNAME_FORTEMASSO,
        "ar_address_barrilito.pdf": AR_ADDRESS_BARRILITO,
    }

    for filename, values in sets.items():
        output_path = OUT_DIR / filename
        fill_form(values, output_path)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

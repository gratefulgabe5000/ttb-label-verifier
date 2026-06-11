"""
WBS 2.3 -- "Good" (all-fields-match) application + label sets, one per
product type (TS-02 / Sec. 2.5 Comparison Matrix).

Each set pairs a synthetic, filled-AcroForm F 5100.31 (Tier 1 -- field
content is what matters here, not extraction tier) with an EXISTING real
label image group from testdata/ (cataloged in manifest.json, WBS 2.1).
Field values are chosen to match what is printed on the label images, so
every Sec. 2.5 comparison rule resolves to MATCH and the expected pipeline
outcome is APPROVE.

Outputs:
  forms/good_spirits_woodford.pdf   Woodford Reserve "Double Oaked" bourbon
  forms/good_wine_lenzmoser.pdf     Lenz Moser "Fete Rose" (Austria)
  forms/good_malt_barrilito.pdf     Cerveza Barrilito (Mexico)

See testdata/test_sets.json for the per-field comparison expectations and
label image references for each set.

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_good_sets.py
"""

from formlib import OUT_DIR, fill_form

# Common Item 14 / signature block defaults shared by all three sets.
_COMMON = {
    "1. REP. ID. NO. (If any)": "",
    "8a. MAILING ADDRESS, IF DIFFERENT": "",
    "9.  FORMULA": "",
    "14a. CERTIFICATE OF LABEL APPROVAL": "/yes",
    "14b. CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL": "/Off",
    "14 b (Fill in State abbreviation)": "",
    "14c. DISTINCTIVE LIQUOR BOTTLE APPROVAL": "/Off",
    "14c.  TOTAL BOTTLE CAPACITY BEFORE CLOSURE (Fill in amount)": "",
    "14d. RESUBMISSION AFTER REJECTION": "/Off",
    "15.  SHOW ANY INFORMATION THAT IS BLOWN, BRANDED, OR EMBOSSED ON THE CONTAINER (e.g., net contents) ONLY IF IT DOES NOT APPEAR ON THE LABELS": "",
    "16.  DATE OF APPLICATION": "06/01/2026",
    "TTB ID": "",
}

# -- Distilled spirits: Woodford Reserve "Double Oaked" (domestic) --------
# Label images: "Woodford Reserve burbon front.jpg"/"front2.jpg" (class/type
# strip + ABV/proof/net contents) and "...back.jpg" (Government Warning,
# producer name/address). Source/Distillery info is publicly listed on the
# product's own back label and TTB COLA records.
SPIRITS_WOODFORD = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "DSP-KY-1",
    "Check Box34": "/Domes",  # Item 3: Source of Product -- Domestic
    "Check Box22": "/Spirits",  # Item 5: Type of Product -- Distilled Spirits
    "6. BRAND NAME (Required)": "Woodford Reserve",
    # Fanciful name left blank: "Double Oaked" appears on the full physical
    # label but not within the cropped label images on file -- leaving this
    # blank avoids an unintended Item 7 mismatch in this all-match set.
    "7. FANCIFUL NAME (If any)": "",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "The Woodford Reserve Distillery\n7855 McCracken Pike\nVersailles, KY 40383"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(859) 555-0148",
    "13.  EMAIL ADDRESS": "compliance@woodfordreserve.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Morgan T. Reyes",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "2",
}

# -- Wine: Lenz Moser "Fete Rose" (imported, Austria) ----------------------
# Label images: "Fete Rose wine.jpg" (brand/fanciful name) and
# "...wine back.jpg" (region "Niederoesterreich", "PRODUCT OF AUSTRIA",
# Government Warning, "IMPORTED BY: niche W. & S., CEDAR KNOLLS, NJ",
# 12% ALC./VOL, 750ML).
WINE_LENZMOSER = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "IMP-NJ-4471",
    "Check Box34": "/Import",  # Item 3: Source of Product -- Imported
    "Check Box22": "/Wine",  # Item 5: Type of Product -- Wine
    "6. BRAND NAME (Required)": "Lenz Moser",
    "7. FANCIFUL NAME (If any)": "Fete Rose",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Niche Import Co.\n21 Ridgedale Avenue\nCedar Knolls, NJ 07927"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    # Label prints "Niederoesterreich" (ASCII transliteration); form uses the
    # standard spelling "Niederosterreich" with diacritic -- exercises the
    # comparator's case/diacritic-tolerant normalized match (FR-059).
    "11.  WINE APPELLATION (If on label)": "Niederosterreich",
    "12.  PHONE NUMBER": "(973) 555-0177",
    "13.  EMAIL ADDRESS": "compliance@nicheimports.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Dana R. Whitfield",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "3",
}

# -- Malt beverage: Cerveza Barrilito (imported, Mexico) -------------------
# Label image: "Cerveza Barrilito.jpg" -- "PRODUCT OF MEXICO", "ALC 3.6% BY
# VOL", "1 QT., 8FL.OZ.", "IMPORTED BY: RR IMPORTACIONES INC., 141 3RD ST,
# UNIT #143 PASSAIC, N.J. 07055-0000", Government Warning.
MALT_BARRILITO = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "IMP-NJ-2208",
    "Check Box34": "/Import",  # Item 3: Source of Product -- Imported
    "Check Box22": "/Malt",  # Item 5: Type of Product -- Malt Beverages
    "6. BRAND NAME (Required)": "Barrilito",
    "7. FANCIFUL NAME (If any)": "",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "RR Importaciones Inc.\n141 3rd St, Unit #143\nPassaic, NJ 07055"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(973) 555-0199",
    "13.  EMAIL ADDRESS": "compliance@rrimportaciones.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Carlos M. Reyes",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "4",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sets = {
        "good_spirits_woodford.pdf": SPIRITS_WOODFORD,
        "good_wine_lenzmoser.pdf": WINE_LENZMOSER,
        "good_malt_barrilito.pdf": MALT_BARRILITO,
    }

    for filename, values in sets.items():
        output_path = OUT_DIR / filename
        fill_form(values, output_path)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

"""
WBS 2.4 -- "Hard failure" application + label sets, one per Sec. 2.5
Parameter Comparison Matrix rule (TS-03 / FR-050-059, FR-066, FR-100-107).

Each set pairs a synthetic, filled-AcroForm F 5100.31 with an EXISTING real
label image group from testdata/ (cataloged in manifest.json, WBS 2.1).
All twelve named rules are exercised by single-field departures from the
WBS 2.3 "good" baselines (build_good_sets.SPIRITS_WOODFORD, plus two new
baselines below); every OTHER field continues to MATCH its label images, so
each fixture isolates exactly one comparison failure (the lone exception is
hf_govtwarning_twelv31.pdf, which has an unavoidable secondary Applicant
Address failure -- see its comment below).

Rule -> fixture map (Sec. 2.5 Comparison Matrix):
  1.  Brand Name (Item 6)              -> hf_brandname_woodford.pdf
  2.  Fanciful Name (Item 7)           -> hf_fancifulname_woodford.pdf
  3.  Country of Origin (Item 3)       -> hf_countryoforigin_woodford.pdf
  4.  Product/Class-Type (Item 5)      -> hf_producttype_fortemasso.pdf
  5.  Applicant Name (Item 8)          -> hf_applicantname_woodford.pdf
  6.  Applicant Address (Item 8)       -> hf_applicantaddress_woodford.pdf
  7.  Grape Varietals (Item 10)        -> hf_grapevarietals_rossoveneto.pdf
  8.  Wine Appellation (Item 11)       -> hf_wineappellation_rossoveneto.pdf
  9.  Type 14b "for sale in [STATE]"   -> hf_14b_woodford.pdf
  10. Government Warning Statement     -> hf_govtwarning_twelv31.pdf
  11. Alcohol by Volume                -> hf_abv_woodford.pdf
  12. Net Contents                     -> hf_netcontents_woodford.pdf

See testdata/test_sets.json for the per-field comparison expectations and
label image references for each set.

Usage:
    testdata/.venv/Scripts/python.exe testdata/build_hard_failure_sets.py
"""

from formlib import OUT_DIR, fill_form
from build_good_sets import _COMMON, SPIRITS_WOODFORD

# ---------------------------------------------------------------------------
# Woodford Reserve variants -- single-field departures from SPIRITS_WOODFORD
# (WBS 2.3's good_spirits_woodford.pdf baseline / "Woodford Reserve burbon
# front.jpg"/"front2.jpg"/"back.jpg"). Each variant changes exactly ONE
# Sec. 2.5 comparison-matrix field; every other field is identical to
# SPIRITS_WOODFORD and continues to MATCH the label images.
# ---------------------------------------------------------------------------

# -- Rule 1: Brand Name (Item 6) ---------------------------------------------
# Label reads "WOODFORD RESERVE"; form claims a different (real, but wrong)
# brand belonging to the same parent company.
HF_BRAND_WOODFORD = {
    **SPIRITS_WOODFORD,
    "6. BRAND NAME (Required)": "Old Forester",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "5",
}

# -- Rule 2: Fanciful Name (Item 7) ------------------------------------------
# "Double Oaked" is the same name WBS 2.3 deliberately left blank because it
# does not appear within the cropped label images on file -- here it is
# claimed outright, producing the Item 7 mismatch 2.3 was designed to avoid.
HF_FANCIFUL_WOODFORD = {
    **SPIRITS_WOODFORD,
    "7. FANCIFUL NAME (If any)": "Double Oaked",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "6",
}

# -- Rule 3: Country of Origin (Item 3 -> Imported) --------------------------
# Form declares "Imported", but the label affirmatively states "PRODUCED BY
# THE WOODFORD RESERVE DISTILLERY, VERSAILLES, KENTUCKY" and carries no
# country-of-origin marking -- the Imported declaration directly contradicts
# the label's domestic-production statement.
HF_ORIGIN_WOODFORD = {
    **SPIRITS_WOODFORD,
    "Check Box34": "/Import",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "7",
}

# -- Rule 9: Type 14b "For sale in [STATE] only" -----------------------------
# Domestic distilled spirits are 14b-eligible (non-malt), so the application
# itself is well-formed; but no "FOR SALE IN OHIO ONLY" (or any state)
# statement appears on any submitted label image.
HF_14B_WOODFORD = {
    **SPIRITS_WOODFORD,
    "14a. CERTIFICATE OF LABEL APPROVAL": "/Off",
    "14b. CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL": "/yes",
    "14 b (Fill in State abbreviation)": "OH",
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "8",
}

# -- Rule 5: Applicant Name (Item 8) -----------------------------------------
# Same address as the label's "...VERSAILLES, KENTUCKY", but a different (and
# real) producer name -- the address half matches while the name half does
# not.
HF_APPLICANT_NAME_WOODFORD = {
    **SPIRITS_WOODFORD,
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Old Forester Distillery\n7855 McCracken Pike\nVersailles, KY 40383"
    ),
    "SERIAL NUMBER 3": "0",
    "SERIAL NUMBER 4": "9",
}

# -- Rule 6: Applicant Address (Item 8) --------------------------------------
# Same producer name and city ("Versailles") as the label, but a different
# state (Versailles, IN exists as a real town) -- an out-of-state address
# change, which Sec. 2.6's "address change within same state" allowable
# revision does NOT cover.
HF_APPLICANT_ADDRESS_WOODFORD = {
    **SPIRITS_WOODFORD,
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "The Woodford Reserve Distillery\n7855 McCracken Pike\nVersailles, IN 47042"
    ),
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "0",
}

# -- Rule 11: Alcohol by Volume (all products, via Item 9 / Formula) --------
# F 5100.31 has no dedicated ABV field, but Item 9 ("FORMULA") records the
# TTB-approved formula (TTB F 5100.51) a product was bottled under -- and 27
# CFR 5.65 requires the label's stated alcohol content to conform to that
# approved formula. Here Item 9 references a formula approved at 40.0%
# ALC/VOL, but the label states "45.2% ALC/VOL (90.4 PROOF)" -- the labeled
# ABV does not match the formula-approved ABV.
HF_ABV_WOODFORD = {
    **SPIRITS_WOODFORD,
    "9.  FORMULA": "TTB Formula #2019-KY-00341 (approved at 40.0% ALC/VOL)",
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "6",
}

# -- Rule 12: Net Contents (all products, via Item 15) -----------------------
# Item 15 declares an embossed/blown net contents of "1 LITER", but the
# submitted label images print "750 mL" -- two conflicting net-contents
# declarations for the same product (27 CFR 5.203 / 4.37 / 7.43 require a
# single, consistent declaration).
HF_NETCONTENTS_WOODFORD = {
    **SPIRITS_WOODFORD,
    "15.  SHOW ANY INFORMATION THAT IS BLOWN, BRANDED, OR EMBOSSED ON THE CONTAINER (e.g., net contents) ONLY IF IT DOES NOT APPEAR ON THE LABELS": (
        "NET CONTENTS 1 LITER BLOWN INTO BASE OF BOTTLE"
    ),
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "1",
}

# ---------------------------------------------------------------------------
# Rosso Veneto "Duo" (imported wine, Italy) -- new baseline for Grape
# Varietals (Item 10) and Wine Appellation (Item 11) hard failures.
#
# Label images: "Rosso Veneto wine front.jpg" (brand "DUO", winemakers Mirko
# Sella / Enrico Marcato, "Rosso Veneto Indicazione Geografica Tipica",
# "Ronca - Italia", vintage 2016) and "...wine back.jpg" ('"DUO" APPASSIMENTO
# PROJECT', blend "Corvina 50% and Cabernet Franc 50%", "Imported by: MARCATO
# DIRECT, Addison, IL 60108", "Alc. 14,5% by Vol. - Net Cont. 750 mL",
# Government Warning).
#
# Note: manifest.json's brand_name for product_key "rosso_veneto" is "Rosso
# Veneto" (derived from the filename), but "Rosso Veneto" is itself the
# wine's IGT appellation/class designation as printed on the label -- the
# brand actually printed on the bottle is "Duo". Item 6 below uses "Duo" to
# match the label, mirroring the WBS 2.3 "Lenz Moser"/"Fete Rose"
# brand-name-vs-fanciful-name distinction.
# ---------------------------------------------------------------------------
WINE_ROSSOVENETO = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "IMP-IL-5519",
    "Check Box34": "/Import",
    "Check Box22": "/Wine",
    "6. BRAND NAME (Required)": "Duo",
    "7. FANCIFUL NAME (If any)": "Appassimento Project",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Marcato Direct\n1200 Lake Street\nAddison, IL 60108"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "Corvina, Cabernet Franc",
    "11.  WINE APPELLATION (If on label)": "Rosso Veneto",
    "12.  PHONE NUMBER": "(630) 555-0134",
    "13.  EMAIL ADDRESS": "compliance@marcatodirect.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Renee K. Marcato",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "2",
}

# -- Rule 7: Grape Varietals (Item 10) ---------------------------------------
# Label states the blend is "Corvina 50% and Cabernet Franc 50%"; form claims
# a varietal (Sangiovese) that is not part of that blend.
HF_GRAPEVARIETALS_ROSSOVENETO = {
    **WINE_ROSSOVENETO,
    "10. GRAPE VARIETAL(S) Wine only": "Sangiovese",
    "SERIAL NUMBER 4": "2",
}

# -- Rule 8: Wine Appellation (Item 11) --------------------------------------
# Label states "ROSSO VENETO INDICAZIONE GEOGRAFICA TIPICA" (a Veneto IGT);
# form claims "Chianti Classico", a Tuscany DOCG -- a different region
# entirely.
HF_WINEAPPELLATION_ROSSOVENETO = {
    **WINE_ROSSOVENETO,
    "11.  WINE APPELLATION (If on label)": "Chianti Classico",
    "SERIAL NUMBER 4": "3",
}

# ---------------------------------------------------------------------------
# Rule 4: Product Type (Item 5) vs Class/Type Designation
#
# Forte Masso (imported, MISCLASSIFIED as malt beverages) -- the anomaly
# flagged in manifest.json / DevLog Session 10.
#
# Label images: "Forte Masso beer front.jpg" (brand "FORTEMASSO") and
# "...beer back.jpg" ("FORTEMASSO 2013 BARBERA D'ALBA DENOMINAZIONE DI
# ORIGINE CONTROLLATA RED WINE ... IMPORTED BY: DUE FRATELLI IMPORTS, LLC
# PORTLAND MAINE ... PRODOTTO IN ITALIA / PRODUCT OF ITALY ... 13,5% vol ...
# Government Warning ... AGRICOLE GUSSALLI BERETTA"). The label is
# unambiguously an Italian Barbera d'Alba DOCG red WINE; the application
# below (Check Box22 = /Malt) carries forward the "malt_beverages"
# classification noted in manifest.json -- a genuine Item 5 / class-type
# conflict (FR-100, FR-107). All other fields are chosen to match the label,
# so this fixture isolates the Item 5 conflict.
# ---------------------------------------------------------------------------
HF_PRODUCTTYPE_FORTEMASSO = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "IMP-ME-3307",
    "Check Box34": "/Import",
    "Check Box22": "/Malt",  # <-- deliberate Item 5 / class-type conflict
    "6. BRAND NAME (Required)": "Forte Masso",
    "7. FANCIFUL NAME (If any)": "",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Due Fratelli Imports, LLC\n88 Marginal Way\nPortland, ME 04101"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(207) 555-0163",
    "13.  EMAIL ADDRESS": "compliance@duefratelliimports.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Lena M. Caruso",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "4",
}

# ---------------------------------------------------------------------------
# Rule 10: Government Warning Statement (all products)
#
# Twelv3 "Velvet Berry" Liqueur (domestic) -- manifest.json product_key
# "twelv_31" has only ONE label image on file: "Twelv 31 liqeur front.jpg".
# That image shows brand "TWELV3", fanciful name "Velvet Berry Liqueur", and
# "20% ALC./VOL.  40 PROOF  750 ML" -- but no Government Warning statement and
# no producer/bottler name or address. The form below is otherwise complete
# and internally consistent (a real producer/address is asserted, since the
# applicant would know its own info even if it is not visible in this single
# cropped image); the Government Warning therefore cannot be located on any
# submitted label image -- a hard failure caused by an incomplete image
# submission rather than a form/label value mismatch. Applicant Name/Address
# is similarly unverifiable from this image alone (see test_sets.json note);
# Rule 6's dedicated coverage is hf_applicantaddress_woodford.pdf above.
# ---------------------------------------------------------------------------
HF_GOVTWARNING_TWELV31 = {
    **_COMMON,
    "2.  PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)": "DSP-NY-20087",
    "Check Box34": "/Domes",
    "Check Box22": "/Spirits",
    "6. BRAND NAME (Required)": "Twelv3",
    "7. FANCIFUL NAME (If any)": "Velvet Berry",
    "8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC": (
        "Twelv3 Spirits Co.\n450 Industrial Pkwy\nBrooklyn, NY 11222"
    ),
    "10. GRAPE VARIETAL(S) Wine only": "",
    "11.  WINE APPELLATION (If on label)": "",
    "12.  PHONE NUMBER": "(718) 555-0190",
    "13.  EMAIL ADDRESS": "compliance@twelv3spirits.com",
    "18.  PRINT NAME OF APPLICANT OR AUTHORIZED AGENT": "Priya N. Castellanos",
    "YEAR 1": "2",
    "YEAR 2": "6",
    "SERIAL NUMBER 1": "0",
    "SERIAL NUMBER 2": "0",
    "SERIAL NUMBER 3": "1",
    "SERIAL NUMBER 4": "5",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sets = {
        "hf_brandname_woodford.pdf": HF_BRAND_WOODFORD,
        "hf_fancifulname_woodford.pdf": HF_FANCIFUL_WOODFORD,
        "hf_countryoforigin_woodford.pdf": HF_ORIGIN_WOODFORD,
        "hf_14b_woodford.pdf": HF_14B_WOODFORD,
        "hf_applicantname_woodford.pdf": HF_APPLICANT_NAME_WOODFORD,
        "hf_applicantaddress_woodford.pdf": HF_APPLICANT_ADDRESS_WOODFORD,
        "hf_netcontents_woodford.pdf": HF_NETCONTENTS_WOODFORD,
        "hf_grapevarietals_rossoveneto.pdf": HF_GRAPEVARIETALS_ROSSOVENETO,
        "hf_wineappellation_rossoveneto.pdf": HF_WINEAPPELLATION_ROSSOVENETO,
        "hf_producttype_fortemasso.pdf": HF_PRODUCTTYPE_FORTEMASSO,
        "hf_govtwarning_twelv31.pdf": HF_GOVTWARNING_TWELV31,
        "hf_abv_woodford.pdf": HF_ABV_WOODFORD,
    }

    for filename, values in sets.items():
        output_path = OUT_DIR / filename
        fill_form(values, output_path)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

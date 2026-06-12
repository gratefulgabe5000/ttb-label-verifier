"""Stage 5: Comparison Engine (WBS 7.0, FR-050-059, FR-066, FR-100-107, DevLog Section 3.2 Stage 5).

Each rule below compares one Form Part I field (Stage 3, `form_parameters`) against
the corresponding label element (Stage 4, `label_parameters`, possibly spread across
several label images) and returns zero, one, or many `FieldComparison` results.
A rule returns `None` when the FR explicitly says "no comparison record SHALL be
generated" for that application (e.g. a blank Item 7/11, or a non-Wine product).

Outcome classification (FR-058): MATCH | HARD_FAILURE | POSSIBLE_ALLOWABLE |
MISSING_FROM_LABEL | MISSING_FROM_FORM. For every rule implemented here, a field
that is wholly absent from every label image is itself the failure condition
(FR-056/066/100/104/105/106/107 all specify HARD_FAILURE on absence), so
`resolve_multi_image`'s literal MISSING_FROM_LABEL outcome (7.1) is converted to
HARD_FAILURE by `_missing_to_hard_failure` before being returned to the caller.

Section V Allowable-Revision mapping (7.5, DevLog Section 2.6): this engine can only
recognize two of the 41 Section V revision types from image inspection --
item 3b (spelling/case/punctuation/font, FR-057/059) and item 19 (name/address
change within the same state, FR-103). Any other mismatch is HARD_FAILURE.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.application import Application
from models.comparison import Comparison
from models.form_parameter import FormParameter
from models.label_parameter import LabelParameter
from services.label_extraction import _normalize_for_comparison

# ---------------------------------------------------------------------------
# Section V Allowable-Revision references this engine can recognize (7.5)
# ---------------------------------------------------------------------------

SECTION_V_SPELLING_CASE_PUNCTUATION = "3b"  # "change type size, font, spelling, case, or punctuation" -- All
SECTION_V_IN_STATE_ADDRESS = "19"  # "change ... name/address within the same state" -- All

# US state abbreviation -> full name, for Type 14b (7.4) and address (7.10) checks.
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Keywords that indicate a label's class/type designation (7.8) is consistent with
# the form's declared Item 5 product type.
PRODUCT_TYPE_KEYWORDS = {
    "wine": ["wine", "vino", "vin", "wein", "champagne", "cava", "sparkling"],
    "distilled_spirits": [
        "whiskey", "whisky", "bourbon", "vodka", "gin", "rum", "tequila", "brandy",
        "liqueur", "spirit", "scotch", "cognac", "mezcal",
    ],
    "malt_beverages": ["beer", "cerveza", "ale", "lager", "malt", "stout", "porter", "bier"],
}

# Plausible ABV ranges per product type (7.13).
ABV_RANGES = {
    "wine": (0.5, 24.0),
    "distilled_spirits": (20.0, 80.0),
    "malt_beverages": (0.5, 16.0),
}


@dataclass
class FieldComparison:
    """One row to be persisted to `comparisons` (FR-058)."""

    field_name: str
    form_value: str | None
    label_value: str | None
    result: str
    section_v_ref: str | None = None
    note: str | None = None
    label_image_id: int | None = None


# ---------------------------------------------------------------------------
# 7.1 -- Multi-image resolution helper (A-10, IA-18, FR-038)
# ---------------------------------------------------------------------------


@dataclass
class ResolvedField:
    result: str  # "MATCH" | "MISSING_FROM_LABEL" | whatever `classify_mismatch` returns
    label_value: str | None
    label_image_id: int | None
    section_v_ref: str | None = None
    note: str | None = None


def resolve_multi_image(
    label_parameters: list[LabelParameter],
    field_name: str,
    form_value: str | None,
    *,
    matches,
    classify_mismatch,
) -> ResolvedField:
    """A form value is "on label" if found on *any* associated label image (7.1).

    - If any image's value satisfies `matches(form_value, label_value)`, that image's
      value is a MATCH and its `label_image_id` is returned (for annotation placement).
    - Otherwise, the highest-confidence candidate (across all images that reported this
      field) is classified via `classify_mismatch(form_value, label_value)`, which
      returns `(result, section_v_ref, note)`.
    - If no image reports this field at all, the result is MISSING_FROM_LABEL.
    """
    candidates = [lp for lp in label_parameters if lp.field_name == field_name and lp.field_value]
    if not candidates:
        return ResolvedField("MISSING_FROM_LABEL", None, None)

    for lp in candidates:
        if matches(form_value, lp.field_value):
            return ResolvedField("MATCH", lp.field_value, lp.label_image_id)

    best = max(candidates, key=lambda lp: lp.confidence or 0.0)
    result, section_v_ref, note = classify_mismatch(form_value, best.field_value)
    return ResolvedField(result, best.field_value, best.label_image_id, section_v_ref, note)


def _missing_to_hard_failure(resolved: ResolvedField, missing_note: str) -> tuple[str, str | None, str | None]:
    """Every rule below treats "absent from every label image" as HARD_FAILURE."""
    if resolved.result == "MISSING_FROM_LABEL":
        return "HARD_FAILURE", None, missing_note
    return resolved.result, resolved.section_v_ref, resolved.note


# ---------------------------------------------------------------------------
# Shared text-comparison helpers (7.5, FR-051/057/059/100/102/105)
# ---------------------------------------------------------------------------


def _strip_punctuation(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _normalize_for_comparison(text))


def text_matches(form_value: str | None, label_value: str) -> bool:
    """Case-insensitive, whitespace-normalized exact match (FR-051)."""
    if not form_value:
        return False
    return _normalize_for_comparison(form_value) == _normalize_for_comparison(label_value)


def classify_text_mismatch(form_value: str | None, label_value: str) -> tuple[str, str | None, str | None]:
    """A spacing/punctuation/case-only difference is POSSIBLE_ALLOWABLE under Sec. V
    item 3b (FR-052/057/059); any other difference is HARD_FAILURE."""
    if form_value and _strip_punctuation(form_value) == _strip_punctuation(label_value):
        return (
            "POSSIBLE_ALLOWABLE",
            SECTION_V_SPELLING_CASE_PUNCTUATION,
            "Differs from the label only in spacing, punctuation, or letter case "
            "(Sec. V item 3b: change type size, font, spelling, case, or punctuation).",
        )
    return "HARD_FAILURE", None, None


def _form_value(form_parameters: dict[str, FormParameter], field_name: str) -> str | None:
    fp = form_parameters.get(field_name)
    if fp is None or fp.field_value is None:
        return None
    value = fp.field_value.strip()
    return value or None


# ---------------------------------------------------------------------------
# 7.10 helper -- US state extraction for in-state address changes (Sec. V item 19)
# ---------------------------------------------------------------------------


def _extract_state(address: str | None) -> str | None:
    if not address:
        return None
    normalized = _normalize_for_comparison(address)
    for code, name in US_STATES.items():
        if _normalize_for_comparison(name) in normalized:
            return code
    for token in re.findall(r"\b[A-Z]{2}\b", address):
        if token in US_STATES:
            return token
    return None


def classify_address_mismatch(form_value: str | None, label_value: str) -> tuple[str, str | None, str | None]:
    """An address mismatch limited to an in-state change is POSSIBLE_ALLOWABLE under
    Sec. V item 19 (FR-103); any other mismatch (including a different state) is
    HARD_FAILURE."""
    form_state = _extract_state(form_value)
    label_state = _extract_state(label_value)
    if form_state and label_state and form_state == label_state:
        return (
            "POSSIBLE_ALLOWABLE",
            SECTION_V_IN_STATE_ADDRESS,
            f"Address differs from the label, but both are in {US_STATES[form_state]} "
            "(Sec. V item 19: change of name/address within the same state).",
        )
    return "HARD_FAILURE", None, None


# ---------------------------------------------------------------------------
# 7.2 -- Brand Name comparison (FR-050-052)
# ---------------------------------------------------------------------------


def compare_brand_name(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    form_value = _form_value(form_params, "brand_name")
    if not form_value:
        return None

    resolved = resolve_multi_image(
        label_params, "brand_name", form_value, matches=text_matches, classify_mismatch=classify_text_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "Brand name not found on any submitted label image."
    )
    return FieldComparison("brand_name", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.3 -- Government Warning comparison (FR-053-055)
# ---------------------------------------------------------------------------


def compare_government_warning(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison:
    present: list[tuple[LabelParameter, dict]] = []
    for lp in label_params:
        if lp.field_name != "government_warning" or not lp.field_value:
            continue
        try:
            data = json.loads(lp.field_value)
        except (TypeError, ValueError):
            continue
        if data.get("text_present"):
            present.append((lp, data))

    if not present:
        return FieldComparison(
            "government_warning",
            None,
            None,
            "HARD_FAILURE",
            None,
            "Government Warning statement (27 CFR § 16.21) not found on any submitted label image.",
            None,
        )

    for lp, data in present:
        if data.get("text_exact_match") and data.get("header_all_caps") and data.get("header_bold"):
            return FieldComparison("government_warning", None, lp.field_value, "MATCH", None, None, lp.label_image_id)

    best_lp, best_data = max(present, key=lambda pair: pair[0].confidence or 0.0)
    failures = []
    if not best_data.get("text_exact_match"):
        failures.append("the statement text does not exactly match 27 CFR § 16.21")
    if not best_data.get("header_all_caps"):
        failures.append('"GOVERNMENT WARNING:" is not in all capital letters')
    if not best_data.get("header_bold"):
        failures.append('"GOVERNMENT WARNING:" is not bold')
    note = "; ".join(failures) + "."
    return FieldComparison("government_warning", None, best_lp.field_value, "HARD_FAILURE", None, note, best_lp.label_image_id)


# ---------------------------------------------------------------------------
# 7.4 -- Type 14b "for sale in [STATE]" check (FR-056)
# ---------------------------------------------------------------------------


def compare_type_14b(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    if application.application_type != "14b":
        return None

    app_type_fp = form_params.get("application_type")
    exemption_state_code = None
    if app_type_fp and app_type_fp.field_value:
        try:
            app_type = json.loads(app_type_fp.field_value)
        except (TypeError, ValueError):
            app_type = {}
        exemption_state_code = app_type.get("exemption_state")

    state_name = US_STATES.get((exemption_state_code or "").upper(), exemption_state_code)
    if not state_name:
        return FieldComparison(
            "for_sale_in_state",
            "Item 14b: exemption state not specified",
            None,
            "HARD_FAILURE",
            None,
            "Item 14b is checked, but no exemption state was declared on the application.",
            None,
        )

    form_value = f"Item 14b: For sale in {state_name} only"
    missing_note = (
        f'No "FOR SALE IN {state_name.upper()} ONLY" statement found on any submitted label image '
        f"(Item 14b declares an exemption restricted to {state_name})."
    )

    def matches(_form_value: str | None, label_value: str) -> bool:
        return _normalize_for_comparison(state_name) in _normalize_for_comparison(label_value)

    def classify_mismatch(_form_value: str | None, _label_value: str) -> tuple[str, str | None, str | None]:
        return "HARD_FAILURE", None, missing_note

    resolved = resolve_multi_image(
        label_params, "for_sale_in_state", form_value, matches=matches, classify_mismatch=classify_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(resolved, missing_note)
    return FieldComparison("for_sale_in_state", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.6 -- Country of Origin comparison (A-17, FR-066)
# ---------------------------------------------------------------------------


def compare_country_of_origin(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    if application.source != "imported":
        return None

    def matches(_form_value: str | None, label_value: str) -> bool:
        return bool(label_value and label_value.strip())

    def classify_mismatch(_form_value: str | None, _label_value: str) -> tuple[str, str | None, str | None]:
        return "HARD_FAILURE", None, None

    resolved = resolve_multi_image(
        label_params, "country_of_origin", None, matches=matches, classify_mismatch=classify_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved,
        "No country-of-origin marking found on any submitted label image, "
        "but Item 3 declares this product Imported.",
    )
    return FieldComparison(
        "country_of_origin", "Imported (Item 3)", resolved.label_value, result, section_v_ref, note, resolved.label_image_id
    )


# ---------------------------------------------------------------------------
# 7.7 -- Fanciful Name comparison (Item 7, FR-100)
# ---------------------------------------------------------------------------


def compare_fanciful_name(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    form_value = _form_value(form_params, "fanciful_name")
    if not form_value:
        return None

    resolved = resolve_multi_image(
        label_params, "fanciful_name", form_value, matches=text_matches, classify_mismatch=classify_text_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "Fanciful name not found on any submitted label image."
    )
    return FieldComparison("fanciful_name", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.8 -- Product Type / Class-Type consistency (Item 5, FR-101)
# ---------------------------------------------------------------------------


def compare_product_type(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    form_value = application.product_type
    if not form_value:
        return None

    keywords = PRODUCT_TYPE_KEYWORDS.get(form_value, [])

    def matches(_form_value: str | None, label_value: str) -> bool:
        text = _normalize_for_comparison(label_value)
        return any(keyword in text for keyword in keywords)

    def classify_mismatch(_form_value: str | None, label_value: str) -> tuple[str, str | None, str | None]:
        return (
            "HARD_FAILURE",
            None,
            f'Label class/type designation ("{label_value}") is inconsistent with the '
            f"declared product type ({form_value.replace('_', ' ')}).",
        )

    resolved = resolve_multi_image(
        label_params, "class_type_designation", form_value, matches=matches, classify_mismatch=classify_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "No class/type designation found on any submitted label image."
    )
    return FieldComparison("product_type", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.9 -- Applicant Name comparison (Item 8, FR-102)
# ---------------------------------------------------------------------------


def compare_applicant_name(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    form_value = _form_value(form_params, "applicant_name") or (application.applicant_name or None)
    if not form_value:
        return None

    resolved = resolve_multi_image(
        label_params, "bottler_name", form_value, matches=text_matches, classify_mismatch=classify_text_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "No bottler/producer name found on any submitted label image."
    )
    return FieldComparison("applicant_name", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.10 -- Applicant Address comparison (Item 8/8a, FR-103)
# ---------------------------------------------------------------------------


def compare_applicant_address(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    form_value = _form_value(form_params, "applicant_address") or _form_value(form_params, "mailing_address")
    if not form_value:
        return None

    resolved = resolve_multi_image(
        label_params, "bottler_address", form_value, matches=text_matches, classify_mismatch=classify_address_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "No bottler/producer address found on any submitted label image."
    )
    return FieldComparison("applicant_address", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.11 -- Grape Varietals comparison (Item 10, Wine only, FR-104)
# ---------------------------------------------------------------------------


def compare_grape_varietals(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> list[FieldComparison] | None:
    if application.product_type != "wine":
        return None

    raw = _form_value(form_params, "grape_varietals")
    if not raw:
        return None
    try:
        varietals = json.loads(raw)
    except (TypeError, ValueError):
        varietals = None
    if not varietals:
        return None

    label_candidates = [lp for lp in label_params if lp.field_name == "grape_varietals" and lp.field_value]
    combined_label_value = ", ".join(lp.field_value for lp in label_candidates) or None
    fallback_image_id = label_candidates[0].label_image_id if label_candidates else None

    comparisons: list[FieldComparison] = []
    for varietal in varietals:
        match = next(
            (lp for lp in label_candidates if _normalize_for_comparison(varietal) in _normalize_for_comparison(lp.field_value)),
            None,
        )
        if match is not None:
            comparisons.append(FieldComparison("grape_varietals", varietal, match.field_value, "MATCH", None, None, match.label_image_id))
        else:
            comparisons.append(
                FieldComparison(
                    "grape_varietals",
                    varietal,
                    combined_label_value,
                    "HARD_FAILURE",
                    None,
                    f'"{varietal}" does not appear among the grape varietals found on any submitted label image.',
                    fallback_image_id,
                )
            )
    return comparisons


# ---------------------------------------------------------------------------
# 7.12 -- Wine Appellation comparison (Item 11, Wine only, FR-105)
# ---------------------------------------------------------------------------


def compare_wine_appellation(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison | None:
    if application.product_type != "wine":
        return None

    form_value = _form_value(form_params, "wine_appellation")
    if not form_value:
        return None

    resolved = resolve_multi_image(
        label_params, "wine_appellation", form_value, matches=text_matches, classify_mismatch=classify_text_mismatch
    )
    result, section_v_ref, note = _missing_to_hard_failure(
        resolved, "No wine appellation found on any submitted label image."
    )
    return FieldComparison("wine_appellation", form_value, resolved.label_value, result, section_v_ref, note, resolved.label_image_id)


# ---------------------------------------------------------------------------
# 7.13 -- ABV presence + product-type consistency check (FR-106)
# ---------------------------------------------------------------------------


def _extract_abv(label_value: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", label_value)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def compare_abv(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison:
    candidates = [lp for lp in label_params if lp.field_name == "alcohol_content" and lp.field_value]
    if not candidates:
        return FieldComparison(
            "alcohol_content", None, None, "HARD_FAILURE", None,
            "No Alcohol by Volume (ABV) value found on any submitted label image.", None,
        )

    abv_range = ABV_RANGES.get(application.product_type)
    for lp in candidates:
        abv = _extract_abv(lp.field_value)
        if abv is not None and (abv_range is None or abv_range[0] <= abv <= abv_range[1]):
            return FieldComparison("alcohol_content", None, lp.field_value, "MATCH", None, None, lp.label_image_id)

    best = max(candidates, key=lambda lp: lp.confidence or 0.0)
    abv = _extract_abv(best.field_value)
    if abv is None:
        note = f'Could not parse an ABV percentage from the label value ("{best.field_value}").'
    else:
        note = (
            f"ABV value ({best.field_value}) is inconsistent with the declared product type "
            f"({(application.product_type or 'unknown').replace('_', ' ')})."
        )
    return FieldComparison("alcohol_content", None, best.field_value, "HARD_FAILURE", None, note, best.label_image_id)


# ---------------------------------------------------------------------------
# 7.14 -- Net Contents presence check (FR-107)
# ---------------------------------------------------------------------------


def compare_net_contents(
    form_params: dict[str, FormParameter], application: Application, label_params: list[LabelParameter]
) -> FieldComparison:
    candidates = [lp for lp in label_params if lp.field_name == "net_contents" and lp.field_value]
    if not candidates:
        return FieldComparison(
            "net_contents", None, None, "HARD_FAILURE", None,
            "No Net Contents value found on any submitted label image.", None,
        )

    best = max(candidates, key=lambda lp: lp.confidence or 0.0)
    return FieldComparison("net_contents", None, best.field_value, "MATCH", None, None, best.label_image_id)


# ---------------------------------------------------------------------------
# Orchestration (7.0)
# ---------------------------------------------------------------------------

COMPARISON_RULES = [
    compare_brand_name,
    compare_government_warning,
    compare_type_14b,
    compare_country_of_origin,
    compare_fanciful_name,
    compare_product_type,
    compare_applicant_name,
    compare_applicant_address,
    compare_grape_varietals,
    compare_wine_appellation,
    compare_abv,
    compare_net_contents,
]


def run_comparisons(
    form_parameters: list[FormParameter],
    application: Application,
    label_parameters: list[LabelParameter],
) -> list[FieldComparison]:
    """Run every comparison rule (7.2-7.14) and return all generated `FieldComparison` rows."""
    form_params = {fp.field_name: fp for fp in form_parameters}

    results: list[FieldComparison] = []
    for rule in COMPARISON_RULES:
        outcome = rule(form_params, application, label_parameters)
        if outcome is None:
            continue
        if isinstance(outcome, list):
            results.extend(outcome)
        else:
            results.append(outcome)
    return results


# ---------------------------------------------------------------------------
# 7.15 -- Persistence (FR-058, DevLog Section 3.4)
# ---------------------------------------------------------------------------


def persist_comparisons(db: Session, application: Application, comparisons: list[FieldComparison]) -> None:
    """Replace `comparisons` rows for `application`."""
    db.query(Comparison).filter(Comparison.application_id == application.id).delete()

    for comp in comparisons:
        db.add(
            Comparison(
                application_id=application.id,
                field_name=comp.field_name,
                form_value=comp.form_value,
                label_value=comp.label_value,
                result=comp.result,
                section_v_ref=comp.section_v_ref,
                note=comp.note,
                label_image_id=comp.label_image_id,
            )
        )

    application.status = "COMPARED"
    db.commit()
    db.refresh(application)

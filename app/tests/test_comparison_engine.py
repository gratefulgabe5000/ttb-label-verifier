"""Stage 5 (Comparison Engine, WBS 7.16) tests.

Covers the 7.1 multi-image resolution helper directly, one representative
test per comparison rule (7.2-7.14), persistence (7.15), and a full
`run_comparisons` orchestration sanity check.
"""

import json

import pytest

from models.application import Application
from models.comparison import Comparison
from models.form_parameter import FormParameter
from models.label_parameter import LabelParameter
from services.comparison_engine import (
    ResolvedField,
    _missing_to_hard_failure,
    classify_text_mismatch,
    compare_abv,
    compare_applicant_address,
    compare_applicant_name,
    compare_brand_name,
    compare_country_of_origin,
    compare_fanciful_name,
    compare_field_of_vision,
    compare_government_warning,
    compare_grape_varietals,
    compare_net_contents,
    compare_product_type,
    compare_type_14b,
    compare_wine_appellation,
    persist_comparisons,
    resolve_multi_image,
    run_comparisons,
    text_matches,
)
from services.label_extraction import GOVERNMENT_WARNING_TEXT


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


def _lp(field_name: str, field_value: str | None, *, label_image_id: int | None = 1, confidence: float = 0.9) -> LabelParameter:
    return LabelParameter(field_name=field_name, field_value=field_value, label_image_id=label_image_id, confidence=confidence)


def _fp(field_name: str, field_value: str | None) -> FormParameter:
    return FormParameter(field_name=field_name, field_value=field_value)


def _app(**kwargs) -> Application:
    defaults = {
        "application_type": "14a",
        "product_type": None,
        "source": "domestic",
        "applicant_name": None,
    }
    defaults.update(kwargs)
    return Application(**defaults)


# ---------------------------------------------------------------------------
# 7.1 -- resolve_multi_image / _missing_to_hard_failure
# ---------------------------------------------------------------------------


class TestResolveMultiImage:
    def test_match_on_non_primary_image(self):
        label_params = [
            _lp("brand_name", "Something Else", label_image_id=1, confidence=0.9),
            _lp("brand_name", "Woodford Reserve", label_image_id=2, confidence=0.8),
        ]
        resolved = resolve_multi_image(
            label_params, "brand_name", "Woodford Reserve", matches=text_matches, classify_mismatch=classify_text_mismatch
        )
        assert resolved.result == "MATCH"
        assert resolved.label_image_id == 2
        assert resolved.label_value == "Woodford Reserve"

    def test_mismatch_classified_via_highest_confidence_candidate(self):
        label_params = [
            _lp("brand_name", "Eagle Valley", label_image_id=1, confidence=0.6),
            _lp("brand_name", "Eagle Valley Reserve", label_image_id=2, confidence=0.95),
        ]
        resolved = resolve_multi_image(
            label_params, "brand_name", "Eagle Ridge", matches=text_matches, classify_mismatch=classify_text_mismatch
        )
        assert resolved.result == "HARD_FAILURE"
        assert resolved.label_image_id == 2
        assert resolved.label_value == "Eagle Valley Reserve"

    def test_mismatch_classified_as_possible_allowable(self):
        label_params = [_lp("brand_name", "FORTEMASSO", label_image_id=1)]
        resolved = resolve_multi_image(
            label_params, "brand_name", "Forte Masso", matches=text_matches, classify_mismatch=classify_text_mismatch
        )
        assert resolved.result == "POSSIBLE_ALLOWABLE"
        assert resolved.section_v_ref == "3b"

    def test_missing_from_label_when_no_image_reports_field(self):
        label_params = [_lp("brand_name", "Woodford Reserve", label_image_id=1)]
        resolved = resolve_multi_image(
            label_params, "wine_appellation", "Napa Valley", matches=text_matches, classify_mismatch=classify_text_mismatch
        )
        assert resolved.result == "MISSING_FROM_LABEL"
        assert resolved.label_value is None
        assert resolved.label_image_id is None


class TestMissingToHardFailure:
    def test_converts_missing_from_label(self):
        resolved = ResolvedField("MISSING_FROM_LABEL", None, None)
        result, section_v_ref, note = _missing_to_hard_failure(resolved, "custom note")
        assert result == "HARD_FAILURE"
        assert section_v_ref is None
        assert note == "custom note"

    def test_passes_through_other_results(self):
        resolved = ResolvedField("MATCH", "value", 1, "3b", "some note")
        result, section_v_ref, note = _missing_to_hard_failure(resolved, "custom note")
        assert result == "MATCH"
        assert section_v_ref == "3b"
        assert note == "some note"


# ---------------------------------------------------------------------------
# 7.2 -- Brand Name (FR-050-052)
# ---------------------------------------------------------------------------


class TestBrandName:
    def test_not_applicable_when_blank(self):
        assert compare_brand_name({}, _app(), []) is None

    def test_match(self):
        form_params = {"brand_name": _fp("brand_name", "Woodford Reserve")}
        label_params = [_lp("brand_name", "Woodford Reserve", label_image_id=1)]
        result = compare_brand_name(form_params, _app(), label_params)
        assert result.result == "MATCH"
        assert result.label_image_id == 1

    def test_possible_allowable_on_spacing_and_case_difference(self):
        form_params = {"brand_name": _fp("brand_name", "Forte Masso")}
        label_params = [_lp("brand_name", "FORTEMASSO", label_image_id=1)]
        result = compare_brand_name(form_params, _app(), label_params)
        assert result.result == "POSSIBLE_ALLOWABLE"
        assert result.section_v_ref == "3b"

    def test_hard_failure_on_substantive_mismatch(self):
        form_params = {"brand_name": _fp("brand_name", "Eagle Ridge")}
        label_params = [_lp("brand_name", "Eagle Valley", label_image_id=1)]
        result = compare_brand_name(form_params, _app(), label_params)
        assert result.result == "HARD_FAILURE"

    def test_hard_failure_when_absent_from_label(self):
        form_params = {"brand_name": _fp("brand_name", "Woodford Reserve")}
        result = compare_brand_name(form_params, _app(), [])
        assert result.result == "HARD_FAILURE"
        assert result.label_value is None

    def test_match_via_bottler_name_fallback_when_brand_name_absent(self):
        # 27 CFR 1.A.5.64: when no Brand Name appears on the label, the
        # bottler/importer name-and-address statement is treated as the brand name.
        form_params = {"brand_name": _fp("brand_name", "Woodford Reserve")}
        label_params = [_lp("bottler_name", "The Woodford Reserve Distillery", label_image_id=2)]
        result = compare_brand_name(form_params, _app(source="domestic"), label_params)
        assert result.result == "MATCH"
        assert result.label_image_id == 2
        assert "1.A.5.64" in result.note

    def test_match_via_importer_name_fallback_for_imported_product(self):
        form_params = {"brand_name": _fp("brand_name", "Niche")}
        label_params = [_lp("importer_name", "Niche Import Co.", label_image_id=3)]
        result = compare_brand_name(form_params, _app(source="imported"), label_params)
        assert result.result == "MATCH"
        assert result.label_image_id == 3

    def test_hard_failure_when_absent_and_fallback_does_not_match(self):
        form_params = {"brand_name": _fp("brand_name", "Eagle Ridge")}
        label_params = [_lp("bottler_name", "Some Other Distillery LLC", label_image_id=1)]
        result = compare_brand_name(form_params, _app(source="domestic"), label_params)
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.3 -- Government Warning (FR-053-055)
# ---------------------------------------------------------------------------


class TestGovernmentWarning:
    def test_match(self):
        gw_value = json.dumps(
            {
                "text_found": GOVERNMENT_WARNING_TEXT,
                "text_present": True,
                "header_all_caps": True,
                "header_bold": True,
                "text_exact_match": True,
            }
        )
        label_params = [_lp("government_warning", gw_value, label_image_id=1)]
        results = compare_government_warning({}, _app(), label_params)
        by_field = {r.field_name: r for r in results}
        assert by_field["government_warning_text"].result == "MATCH"
        assert by_field["government_warning_caps"].result == "MATCH"
        assert by_field["government_warning_bold"].result == "MATCH"
        assert all(r.label_image_id == 1 for r in results)

    def test_hard_failure_when_absent(self):
        absent_value = json.dumps(
            {"text_found": None, "text_present": False, "header_all_caps": None, "header_bold": None, "text_exact_match": None}
        )
        label_params = [_lp("government_warning", absent_value, label_image_id=1)]
        results = compare_government_warning({}, _app(), label_params)
        assert all(r.result == "HARD_FAILURE" for r in results)
        assert all("not found" in r.note for r in results)

    def test_hard_failure_when_header_not_bold(self):
        gw_value = json.dumps(
            {
                "text_found": GOVERNMENT_WARNING_TEXT,
                "text_present": True,
                "header_all_caps": True,
                "header_bold": False,
                "text_exact_match": True,
            }
        )
        label_params = [_lp("government_warning", gw_value, label_image_id=1)]
        results = compare_government_warning({}, _app(), label_params)
        by_field = {r.field_name: r for r in results}
        assert by_field["government_warning_text"].result == "MATCH"
        assert by_field["government_warning_caps"].result == "MATCH"
        assert by_field["government_warning_bold"].result == "HARD_FAILURE"
        assert "bold" in by_field["government_warning_bold"].note

    def test_match_on_punctuation_only_text_difference(self):
        # Label uses a comma before "(2)" and omits the trailing period, where the
        # statute (27 CFR § 16.21) has a period before "(2)" and ends with one --
        # text content matches, only punctuation differs, so this is still a MATCH.
        label_text = GOVERNMENT_WARNING_TEXT.replace("birth defects. (2)", "birth defects, (2)").rstrip(".")
        gw_value = json.dumps(
            {
                "text_found": label_text,
                "text_present": True,
                "header_all_caps": True,
                "header_bold": True,
                "text_exact_match": False,
            }
        )
        label_params = [_lp("government_warning", gw_value, label_image_id=1)]
        results = compare_government_warning({}, _app(), label_params)
        by_field = {r.field_name: r for r in results}
        assert by_field["government_warning_text"].result == "MATCH"
        assert by_field["government_warning_text"].section_v_ref is None
        assert by_field["government_warning_text"].note is None
        assert by_field["government_warning_caps"].result == "MATCH"
        assert by_field["government_warning_bold"].result == "MATCH"

    def test_match_on_all_caps_and_punctuation_difference(self):
        # Real-world label text: rendered in ALL CAPS, a comma before "(2)" where
        # the statute has a period, and no trailing period -- letter case and
        # punctuation both differ, content matches, so this is still a MATCH.
        label_text = (
            GOVERNMENT_WARNING_TEXT.replace("birth defects. (2)", "birth defects, (2)").rstrip(".").upper()
        )
        gw_value = json.dumps(
            {
                "text_found": label_text,
                "text_present": True,
                "header_all_caps": True,
                "header_bold": True,
                "text_exact_match": False,
            }
        )
        label_params = [_lp("government_warning", gw_value, label_image_id=1)]
        results = compare_government_warning({}, _app(), label_params)
        by_field = {r.field_name: r for r in results}
        assert by_field["government_warning_text"].result == "MATCH"
        assert by_field["government_warning_text"].section_v_ref is None
        assert by_field["government_warning_text"].note is None


# ---------------------------------------------------------------------------
# 7.4 -- Type 14b "for sale in [STATE]" (FR-056)
# ---------------------------------------------------------------------------


class TestType14b:
    def test_not_applicable_for_14a(self):
        assert compare_type_14b({}, _app(application_type="14a"), []) is None

    def test_match(self):
        form_params = {"application_type": _fp("application_type", json.dumps({"checked": ["14b"], "exemption_state": "PA"}))}
        label_params = [_lp("for_sale_in_state", "FOR SALE IN PENNSYLVANIA ONLY", label_image_id=1)]
        result = compare_type_14b(form_params, _app(application_type="14b"), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_when_statement_absent(self):
        form_params = {"application_type": _fp("application_type", json.dumps({"checked": ["14b"], "exemption_state": "OH"}))}
        result = compare_type_14b(form_params, _app(application_type="14b"), [])
        assert result.result == "HARD_FAILURE"
        assert "OHIO" in result.note


# ---------------------------------------------------------------------------
# 7.6 -- Country of Origin (A-17, FR-066)
# ---------------------------------------------------------------------------


class TestCountryOfOrigin:
    def test_not_applicable_when_domestic(self):
        assert compare_country_of_origin({}, _app(source="domestic"), []) is None

    def test_match_when_present(self):
        label_params = [_lp("country_of_origin", "PRODUCT OF AUSTRIA", label_image_id=1)]
        result = compare_country_of_origin({}, _app(source="imported"), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_when_absent(self):
        result = compare_country_of_origin({}, _app(source="imported"), [])
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.7 -- Fanciful Name (Item 7, FR-100)
# ---------------------------------------------------------------------------


class TestFancifulName:
    def test_not_applicable_when_blank(self):
        assert compare_fanciful_name({}, _app(), []) is None

    def test_match(self):
        form_params = {"fanciful_name": _fp("fanciful_name", "Fete Rose")}
        label_params = [_lp("fanciful_name", "Fete Rose", label_image_id=1)]
        result = compare_fanciful_name(form_params, _app(), label_params)
        assert result.result == "MATCH"

    def test_match_ignores_diacritics(self):
        # Forms are routinely typed without accent marks even when the label
        # itself carries them -- "Fete Rose" vs "Fête Rosé" is a MATCH.
        form_params = {"fanciful_name": _fp("fanciful_name", "Fete Rose")}
        label_params = [_lp("fanciful_name", "Fête Rosé", label_image_id=1)]
        result = compare_fanciful_name(form_params, _app(), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_when_absent_from_label(self):
        form_params = {"fanciful_name": _fp("fanciful_name", "Double Oaked")}
        result = compare_fanciful_name(form_params, _app(), [])
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.8 -- Product Type / Class-Type consistency (Item 5, FR-101)
# ---------------------------------------------------------------------------


class TestProductType:
    def test_not_applicable_when_product_type_unset(self):
        assert compare_product_type({}, _app(product_type=None), []) is None

    def test_match(self):
        label_params = [_lp("class_type_designation", "Kentucky Straight Bourbon Whiskey", label_image_id=1)]
        result = compare_product_type({}, _app(product_type="distilled_spirits"), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_on_inconsistent_class_type(self):
        label_params = [_lp("class_type_designation", "Barbera d'Alba DOCG -- Red Wine", label_image_id=1)]
        result = compare_product_type({}, _app(product_type="malt_beverages"), label_params)
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.9 -- Applicant Name (Item 8, FR-102)
# ---------------------------------------------------------------------------


class TestApplicantName:
    def test_match(self):
        form_params = {"applicant_name": _fp("applicant_name", "The Woodford Reserve Distillery")}
        label_params = [_lp("bottler_name", "The Woodford Reserve Distillery", label_image_id=1)]
        result = compare_applicant_name(form_params, _app(), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_on_different_producer(self):
        form_params = {"applicant_name": _fp("applicant_name", "Old Forester Distillery")}
        label_params = [_lp("bottler_name", "The Woodford Reserve Distillery", label_image_id=1)]
        result = compare_applicant_name(form_params, _app(), label_params)
        assert result.result == "HARD_FAILURE"

    def test_match_against_importer_for_imported_product(self):
        # Item 8 (Applicant Name) names the importer, not the foreign producer --
        # the label's bottler_name (the foreign producer) won't match, but
        # importer_name should.
        form_params = {"applicant_name": _fp("applicant_name", "ABC Imports LLC")}
        label_params = [
            _lp("bottler_name", "Cantina Foreign Producer S.r.l.", label_image_id=1),
            _lp("importer_name", "ABC Imports LLC", label_image_id=1),
        ]
        result = compare_applicant_name(form_params, _app(source="imported"), label_params)
        assert result.result == "MATCH"

    def test_mismatch_for_imported_product_classified_against_importer_not_bottler(self):
        # Even when neither label value matches exactly and the bottler has
        # higher OCR/Vision confidence than the importer, an imported
        # product's mismatch must be classified against importer_name (the
        # actual Item 8 applicant) -- not the foreign bottler/producer.
        form_params = {"applicant_name": _fp("applicant_name", "Niche Import Co.")}
        label_params = [
            _lp("bottler_name", "Weinkellerei Lenz Moser AG", label_image_id=1, confidence=0.98),
            _lp("importer_name", "Niche W. & S.", label_image_id=1, confidence=0.95),
        ]
        result = compare_applicant_name(form_params, _app(source="imported"), label_params)
        assert result.label_value == "Niche W. & S."

    def test_hard_failure_when_importer_absent_for_imported_product(self):
        form_params = {"applicant_name": _fp("applicant_name", "ABC Imports LLC")}
        label_params = [_lp("bottler_name", "Cantina Foreign Producer S.r.l.", label_image_id=1)]
        result = compare_applicant_name(form_params, _app(source="imported"), label_params)
        assert result.result == "HARD_FAILURE"
        assert result.label_value is None


# ---------------------------------------------------------------------------
# 7.10 -- Applicant Address (Item 8/8a, FR-103)
# ---------------------------------------------------------------------------


class TestApplicantAddress:
    def test_match(self):
        form_params = {"applicant_address": _fp("applicant_address", "7855 McCracken Pike, Versailles, KY 40383")}
        label_params = [_lp("bottler_address", "7855 McCracken Pike, Versailles, KY 40383", label_image_id=1)]
        result = compare_applicant_address(form_params, _app(), label_params)
        assert result.result == "MATCH"

    def test_match_ignores_case_punctuation_and_zip4(self):
        # Label is ALL CAPS with extra periods and a ZIP+4; form is mixed-case
        # with a plain ZIP5 -- this is a MATCH, not POSSIBLE_ALLOWABLE.
        form_params = {"applicant_address": _fp("applicant_address", "200 Brook Avenue, Unit 5, Passaic, NJ 07055")}
        label_params = [_lp("bottler_address", "200 BROOK AVENUE, UNIT. 5, PASSAIC, N.J. 07055-0000", label_image_id=1)]
        result = compare_applicant_address(form_params, _app(), label_params)
        assert result.result == "MATCH"

    def test_match_against_importer_for_imported_product(self):
        # Item 8/8a (Applicant Address) names the importer's address -- the
        # label's bottler_address (the foreign producer) won't match, but
        # importer_address should.
        form_params = {"applicant_address": _fp("applicant_address", "100 Import Way, Newark, NJ 07102")}
        label_params = [
            _lp("bottler_address", "Via Roma 1, 12051 Alba (CN), Italy", label_image_id=1),
            _lp("importer_address", "100 Import Way, Newark, NJ 07102", label_image_id=1),
        ]
        result = compare_applicant_address(form_params, _app(source="imported"), label_params)
        assert result.result == "MATCH"

    def test_mismatch_for_imported_product_classified_against_importer_not_bottler(self):
        # Even when the foreign bottler_address has higher confidence than
        # importer_address and neither matches exactly, the mismatch must be
        # classified against the importer's address.
        form_params = {"applicant_address": _fp("applicant_address", "21 Ridgedale Avenue, Cedar Knolls, NJ 07927")}
        label_params = [
            _lp("bottler_address", "A-3495 Rohrendorf, Austria", label_image_id=1, confidence=0.98),
            _lp("importer_address", "Cedar Knolls, NJ", label_image_id=1, confidence=0.95),
        ]
        result = compare_applicant_address(form_params, _app(source="imported"), label_params)
        assert result.label_value == "Cedar Knolls, NJ"
        assert result.result == "POSSIBLE_ALLOWABLE"
        assert result.section_v_ref == "19"

    def test_possible_allowable_for_in_state_address_change(self):
        form_params = {"applicant_address": _fp("applicant_address", "200 Brook Avenue, Passaic, NJ 07055")}
        label_params = [_lp("bottler_address", "141 3rd St, Unit #143, Passaic, NJ 07055", label_image_id=1)]
        result = compare_applicant_address(form_params, _app(), label_params)
        assert result.result == "POSSIBLE_ALLOWABLE"
        assert result.section_v_ref == "19"

    def test_hard_failure_for_out_of_state_address_change(self):
        form_params = {"applicant_address": _fp("applicant_address", "7855 McCracken Pike, Versailles, IN 47042")}
        label_params = [_lp("bottler_address", "7855 McCracken Pike, Versailles, KY 40383", label_image_id=1)]
        result = compare_applicant_address(form_params, _app(), label_params)
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.11 -- Grape Varietals (Item 10, Wine only, FR-104)
# ---------------------------------------------------------------------------


class TestGrapeVarietals:
    def test_not_applicable_for_non_wine(self):
        assert compare_grape_varietals({}, _app(product_type="distilled_spirits"), []) is None

    def test_not_applicable_when_item10_blank(self):
        assert compare_grape_varietals({}, _app(product_type="wine"), []) is None

    def test_match_for_each_varietal_present(self):
        form_params = {"grape_varietals": _fp("grape_varietals", json.dumps(["Corvina", "Cabernet Franc"]))}
        label_params = [_lp("grape_varietals", "Corvina 50% and Cabernet Franc 50%", label_image_id=1)]
        results = compare_grape_varietals(form_params, _app(product_type="wine"), label_params)
        assert len(results) == 2
        assert all(r.result == "MATCH" for r in results)

    def test_hard_failure_for_varietal_absent_from_label(self):
        form_params = {"grape_varietals": _fp("grape_varietals", json.dumps(["Sangiovese"]))}
        label_params = [_lp("grape_varietals", "Corvina 50% and Cabernet Franc 50%", label_image_id=1)]
        results = compare_grape_varietals(form_params, _app(product_type="wine"), label_params)
        assert len(results) == 1
        assert results[0].result == "HARD_FAILURE"
        assert results[0].form_value == "Sangiovese"


# ---------------------------------------------------------------------------
# 7.12 -- Wine Appellation (Item 11, Wine only, FR-105)
# ---------------------------------------------------------------------------


class TestWineAppellation:
    def test_not_applicable_when_blank(self):
        assert compare_wine_appellation({}, _app(product_type="wine"), []) is None

    def test_not_applicable_for_non_wine(self):
        form_params = {"wine_appellation": _fp("wine_appellation", "Napa Valley")}
        assert compare_wine_appellation(form_params, _app(product_type="distilled_spirits"), []) is None

    def test_match(self):
        form_params = {"wine_appellation": _fp("wine_appellation", "Napa Valley")}
        label_params = [_lp("wine_appellation", "Napa Valley", label_image_id=1)]
        result = compare_wine_appellation(form_params, _app(product_type="wine"), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_on_different_appellation(self):
        form_params = {"wine_appellation": _fp("wine_appellation", "Chianti Classico")}
        label_params = [_lp("wine_appellation", "Rosso Veneto Indicazione Geografica Tipica", label_image_id=1)]
        result = compare_wine_appellation(form_params, _app(product_type="wine"), label_params)
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# 7.13 -- ABV presence + product-type consistency (FR-106)
# ---------------------------------------------------------------------------


class TestAbv:
    def test_match(self):
        label_params = [_lp("alcohol_content", "45.2% ALC/VOL (90.4 PROOF)", label_image_id=1)]
        result = compare_abv({}, _app(product_type="distilled_spirits"), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_when_absent(self):
        result = compare_abv({}, _app(product_type="wine"), [])
        assert result.result == "HARD_FAILURE"

    def test_hard_failure_when_inconsistent_with_product_type(self):
        label_params = [_lp("alcohol_content", "0.0% ALC/VOL", label_image_id=1)]
        result = compare_abv({}, _app(product_type="wine"), label_params)
        assert result.result == "HARD_FAILURE"

    @pytest.mark.parametrize(
        "text",
        [
            "12% Alcohol by Volume",
            "12% alc/vol",
            "Alc. 12 percent by vol.",
            "Alc 12% by vol",
        ],
    )
    def test_match_for_each_approved_abv_phrasing(self, text):
        # 27 CFR 5.65/7.65/4.36 -- any of these four formats is acceptable.
        label_params = [_lp("alcohol_content", text, label_image_id=1)]
        result = compare_abv({}, _app(product_type="wine"), label_params)
        assert result.result == "MATCH"

    def test_possible_allowable_when_value_correct_but_phrasing_nonconforming(self):
        label_params = [_lp("alcohol_content", "12% Alcohol", label_image_id=1)]
        result = compare_abv({}, _app(product_type="wine"), label_params)
        assert result.result == "POSSIBLE_ALLOWABLE"
        assert result.section_v_ref == "3b"


# ---------------------------------------------------------------------------
# 7.14 -- Net Contents presence check (FR-107)
# ---------------------------------------------------------------------------


class TestNetContents:
    def test_match(self):
        label_params = [_lp("net_contents", "750 mL", label_image_id=1)]
        result = compare_net_contents({}, _app(), label_params)
        assert result.result == "MATCH"

    def test_hard_failure_when_absent(self):
        result = compare_net_contents({}, _app(), [])
        assert result.result == "HARD_FAILURE"


# ---------------------------------------------------------------------------
# Field of Vision check -- Brand Name / Class-Type / ABV (27 CFR 4.38, 5.63(a),
# 7.63(a))
# ---------------------------------------------------------------------------


class TestFieldOfVision:
    def test_match_when_brand_class_and_abv_share_an_image(self):
        label_params = [
            _lp("brand_name", "Woodford Reserve", label_image_id=1),
            _lp("class_type_designation", "Kentucky Straight Bourbon Whiskey", label_image_id=1),
            _lp("alcohol_content", "45.2% ALC/VOL", label_image_id=1),
        ]
        result = compare_field_of_vision({}, _app(source="domestic"), label_params)
        assert result.result == "MATCH"
        assert result.label_image_id == 1

    def test_possible_allowable_when_elements_are_on_different_images(self):
        label_params = [
            _lp("bottler_name", "The Woodford Reserve Distillery", label_image_id=2),
            _lp("class_type_designation", "Kentucky Straight Bourbon Whiskey", label_image_id=1),
            _lp("alcohol_content", "45.2% ALC/VOL", label_image_id=1),
        ]
        result = compare_field_of_vision({}, _app(source="domestic"), label_params)
        assert result.result == "POSSIBLE_ALLOWABLE"
        assert "field of vision" in result.note

    def test_none_when_an_element_is_missing_from_label_entirely(self):
        label_params = [
            _lp("brand_name", "Woodford Reserve", label_image_id=1),
            _lp("class_type_designation", "Kentucky Straight Bourbon Whiskey", label_image_id=1),
        ]
        assert compare_field_of_vision({}, _app(source="domestic"), label_params) is None


# ---------------------------------------------------------------------------
# run_comparisons orchestration
# ---------------------------------------------------------------------------


class TestRunComparisons:
    def test_full_application_approve_path(self):
        application = _app(product_type="distilled_spirits", source="domestic", applicant_name="The Woodford Reserve Distillery")
        form_parameters = [
            _fp("brand_name", "Woodford Reserve"),
            _fp("applicant_name", "The Woodford Reserve Distillery"),
            _fp("applicant_address", "7855 McCracken Pike, Versailles, KY 40383"),
        ]
        gw_value = json.dumps(
            {
                "text_found": GOVERNMENT_WARNING_TEXT,
                "text_present": True,
                "header_all_caps": True,
                "header_bold": True,
                "text_exact_match": True,
            }
        )
        label_parameters = [
            _lp("brand_name", "Woodford Reserve", label_image_id=1),
            _lp("class_type_designation", "Kentucky Straight Bourbon Whiskey", label_image_id=1),
            _lp("bottler_name", "The Woodford Reserve Distillery", label_image_id=1),
            _lp("bottler_address", "7855 McCracken Pike, Versailles, KY 40383", label_image_id=1),
            _lp("government_warning", gw_value, label_image_id=1),
            _lp("alcohol_content", "45.2% ALC/VOL (90.4 PROOF)", label_image_id=1),
            _lp("net_contents", "750 mL", label_image_id=1),
        ]

        results = run_comparisons(form_parameters, application, label_parameters)
        by_field = {r.field_name: r for r in results}

        for field in (
            "brand_name",
            "product_type",
            "applicant_name",
            "applicant_address",
            "government_warning_text",
            "government_warning_caps",
            "government_warning_bold",
            "alcohol_content",
            "net_contents",
        ):
            assert by_field[field].result == "MATCH", field

        # NOT_APPLICABLE rules (Item 7/11 blank, non-imported, non-Wine, 14a) produce no row
        for field in ("fanciful_name", "country_of_origin", "for_sale_in_state", "grape_varietals", "wine_appellation"):
            assert field not in by_field


# ---------------------------------------------------------------------------
# 7.15 -- Persistence (FR-058, DevLog Section 3.4)
# ---------------------------------------------------------------------------


class TestPersistComparisons:
    def test_persist_comparisons(self, db_session):
        from services.comparison_engine import FieldComparison

        application = Application(brand_name="Woodford Reserve", product_type="distilled_spirits", source="domestic")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        comparisons = [
            FieldComparison("brand_name", "Woodford Reserve", "Woodford Reserve", "MATCH", None, None, 1),
            FieldComparison("net_contents", None, None, "HARD_FAILURE", None, "No Net Contents value found.", None),
        ]
        persist_comparisons(db_session, application, comparisons)

        rows = db_session.query(Comparison).filter(Comparison.application_id == application.id).all()
        assert len(rows) == 2
        assert application.status == "COMPARED"

        by_field = {row.field_name: row for row in rows}
        assert by_field["brand_name"].result == "MATCH"
        assert by_field["brand_name"].label_image_id == 1
        assert by_field["net_contents"].result == "HARD_FAILURE"

    def test_persist_comparisons_replaces_existing_rows(self, db_session):
        from services.comparison_engine import FieldComparison

        application = Application()
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        persist_comparisons(db_session, application, [FieldComparison("brand_name", "A", "A", "MATCH")])
        persist_comparisons(db_session, application, [FieldComparison("net_contents", None, "750 mL", "MATCH")])

        rows = db_session.query(Comparison).filter(Comparison.application_id == application.id).all()
        assert len(rows) == 1
        assert rows[0].field_name == "net_contents"

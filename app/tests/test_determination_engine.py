"""Stage 6 (Determination & Reporting, WBS 8.5) tests.

Covers the determination logic (8.1, FR-060-062), hard-failure / allowable-revision
list generation (8.2, FR-063/064), the determination report (8.3, FR-065), and
persistence to `determinations` (8.4).
"""

from datetime import datetime, timezone

import pytest

from models.application import Application
from models.comparison import Comparison
from models.determination import Determination
from models.form_parameter import FormParameter
from models.label_parameter import LabelParameter
from services.determination_engine import (
    build_allowable_revisions,
    build_confidence_scores,
    build_determination_report,
    build_hard_failures,
    determine_recommendation,
    persist_determination,
    run_determination,
)


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


def _comp(
    field_name: str,
    result: str,
    *,
    form_value: str | None = None,
    label_value: str | None = None,
    section_v_ref: str | None = None,
    note: str | None = None,
) -> Comparison:
    return Comparison(
        field_name=field_name,
        form_value=form_value,
        label_value=label_value,
        result=result,
        section_v_ref=section_v_ref,
        note=note,
    )


def _fp(field_name: str, field_value: str | None, confidence: float | None = None) -> FormParameter:
    return FormParameter(field_name=field_name, field_value=field_value, confidence=confidence)


def _lp(field_name: str, field_value: str | None, confidence: float | None = None) -> LabelParameter:
    return LabelParameter(field_name=field_name, field_value=field_value, confidence=confidence)


# ---------------------------------------------------------------------------
# 8.1 -- determine_recommendation (FR-060-062)
# ---------------------------------------------------------------------------


class TestDetermineRecommendation:
    def test_approve_when_all_match(self):
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp("net_contents", "MATCH", label_value="750 mL"),
        ]
        assert determine_recommendation(comparisons) == "APPROVE"

    def test_approve_when_no_comparisons(self):
        assert determine_recommendation([]) == "APPROVE"

    def test_deny_when_one_hard_failure(self):
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image."),
        ]
        assert determine_recommendation(comparisons) == "DENY"

    def test_recommend_exemption_review_when_possible_allowable_and_no_hard_failure(self):
        comparisons = [
            _comp("brand_name", "POSSIBLE_ALLOWABLE", form_value="FORTEMASSO", label_value="Forte Masso", section_v_ref="3b", note="spacing/case diff"),
            _comp("net_contents", "MATCH", label_value="750 mL"),
        ]
        assert determine_recommendation(comparisons) == "RECOMMEND_EXEMPTION_REVIEW"

    def test_hard_failure_takes_precedence_over_possible_allowable(self):
        comparisons = [
            _comp("brand_name", "POSSIBLE_ALLOWABLE", form_value="FORTEMASSO", label_value="Forte Masso", section_v_ref="3b", note="spacing/case diff"),
            _comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image."),
        ]
        assert determine_recommendation(comparisons) == "DENY"


# ---------------------------------------------------------------------------
# 8.2 -- build_hard_failures (FR-063)
# ---------------------------------------------------------------------------


class TestBuildHardFailures:
    def test_only_hard_failures_included(self):
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image."),
        ]
        failures = build_hard_failures(comparisons)
        assert len(failures) == 1
        assert failures[0].field_name == "net_contents"
        assert failures[0].description == "No Net Contents value found on any submitted label image."

    def test_uses_existing_note_as_description(self):
        comparisons = [
            _comp(
                "alcohol_content",
                "HARD_FAILURE",
                label_value="0.0% ALC/VOL",
                note="ABV value (0.0% ALC/VOL) is inconsistent with the declared product type (wine).",
            ),
        ]
        failures = build_hard_failures(comparisons)
        assert failures[0].description == "ABV value (0.0% ALC/VOL) is inconsistent with the declared product type (wine)."

    def test_generates_description_when_note_missing(self):
        comparisons = [
            _comp("brand_name", "HARD_FAILURE", form_value="Eagle Ridge", label_value="Eagle Valley Reserve"),
        ]
        failures = build_hard_failures(comparisons)
        assert len(failures) == 1
        description = failures[0].description
        assert "Brand Name" in description
        assert "Eagle Ridge" in description
        assert "Eagle Valley Reserve" in description

    def test_no_hard_failures_returns_empty_list(self):
        comparisons = [_comp("brand_name", "MATCH", form_value="X", label_value="X")]
        assert build_hard_failures(comparisons) == []


# ---------------------------------------------------------------------------
# 8.2 -- build_allowable_revisions (FR-064)
# ---------------------------------------------------------------------------


class TestBuildAllowableRevisions:
    def test_only_possible_allowable_included(self):
        comparisons = [
            _comp("brand_name", "MATCH", form_value="X", label_value="X"),
            _comp(
                "brand_name",
                "POSSIBLE_ALLOWABLE",
                form_value="FORTEMASSO",
                label_value="Forte Masso",
                section_v_ref="3b",
                note="Differs from the label only in spacing, punctuation, or letter case (Sec. V item 3b: change type size, font, spelling, case, or punctuation).",
            ),
        ]
        revisions = build_allowable_revisions(comparisons)
        assert len(revisions) == 1
        assert revisions[0].field_name == "brand_name"
        assert revisions[0].section_v_ref == "3b"
        assert "Sec. V item 3b" in revisions[0].discrepancy

    def test_no_possible_allowables_returns_empty_list(self):
        comparisons = [_comp("brand_name", "MATCH", form_value="X", label_value="X")]
        assert build_allowable_revisions(comparisons) == []


# ---------------------------------------------------------------------------
# 8.1 + 8.2 -- run_determination (all 3 outcomes + edge cases)
# ---------------------------------------------------------------------------


class TestRunDetermination:
    def test_approve_path(self):
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp("net_contents", "MATCH", label_value="750 mL"),
        ]
        result = run_determination(comparisons)
        assert result.recommendation == "APPROVE"
        assert result.hard_failures == []
        assert result.allowable_revisions == []

    def test_deny_path_with_two_hard_failures(self):
        comparisons = [
            _comp("brand_name", "HARD_FAILURE", form_value="Eagle Ridge", label_value="Eagle Valley Reserve"),
            _comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image."),
        ]
        result = run_determination(comparisons)
        assert result.recommendation == "DENY"
        assert len(result.hard_failures) == 2
        assert result.allowable_revisions == []

    def test_recommend_exemption_review_path_no_hard_failures_with_possible_allowable(self):
        """Edge case from WBS 8.5: no hard failures, but an unresolved possible-allowable."""
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp(
                "applicant_address",
                "POSSIBLE_ALLOWABLE",
                form_value="123 Main St, Lexington, KY",
                label_value="456 Oak Ave, Lexington, KY",
                section_v_ref="19",
                note="Address differs from the label, but both are in Kentucky (Sec. V item 19: change of name/address within the same state).",
            ),
        ]
        result = run_determination(comparisons)
        assert result.recommendation == "RECOMMEND_EXEMPTION_REVIEW"
        assert result.hard_failures == []
        assert len(result.allowable_revisions) == 1
        assert result.allowable_revisions[0].section_v_ref == "19"


# ---------------------------------------------------------------------------
# 8.3 -- build_confidence_scores / build_determination_report (FR-065)
# ---------------------------------------------------------------------------


class TestBuildConfidenceScores:
    def test_form_confidence_overrides_label_confidence(self):
        form_parameters = [_fp("brand_name", "Woodford Reserve", 0.95)]
        label_parameters = [_lp("brand_name", "Woodford Reserve", 0.6)]
        scores = build_confidence_scores(form_parameters, label_parameters)
        assert scores["brand_name"] == 0.95

    def test_label_only_field_included(self):
        form_parameters: list[FormParameter] = []
        label_parameters = [_lp("net_contents", "750 mL", 0.8)]
        scores = build_confidence_scores(form_parameters, label_parameters)
        assert scores["net_contents"] == 0.8

    def test_blank_values_excluded(self):
        form_parameters = [_fp("fanciful_name", None, 0.9)]
        label_parameters = [_lp("wine_appellation", "", 0.7)]
        scores = build_confidence_scores(form_parameters, label_parameters)
        assert "fanciful_name" not in scores
        assert "wine_appellation" not in scores


class TestBuildDeterminationReport:
    def test_report_contains_all_components(self):
        application = Application(id=42, product_type="distilled_spirits")
        comparisons = [
            _comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve"),
            _comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image."),
        ]
        form_parameters = [_fp("brand_name", "Woodford Reserve", 0.95)]
        label_parameters = [_lp("brand_name", "Woodford Reserve", 0.6)]
        result = run_determination(comparisons)
        processed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        report = build_determination_report(application, comparisons, form_parameters, label_parameters, result, processed_at)

        assert report.application_id == 42
        assert report.recommendation == "DENY"
        assert report.comparisons == comparisons
        assert len(report.hard_failures) == 1
        assert report.allowable_revisions == []
        assert report.confidence_scores["brand_name"] == 0.95
        assert report.processed_at == processed_at


# ---------------------------------------------------------------------------
# 8.4 -- persist_determination
# ---------------------------------------------------------------------------


class TestPersistDetermination:
    def test_persist_creates_new_row(self, db_session):
        application = Application(brand_name="Woodford Reserve", product_type="distilled_spirits", status="COMPARED")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        comparisons = [_comp("brand_name", "MATCH", form_value="Woodford Reserve", label_value="Woodford Reserve")]
        result = run_determination(comparisons)
        determination = persist_determination(db_session, application, result)

        assert determination.id is not None
        assert determination.application_id == application.id
        assert determination.recommendation == "APPROVE"
        assert determination.hard_failures_json == "[]"
        assert determination.allowable_json == "[]"
        assert application.status == "DETERMINED"
        assert application.processed_at is not None

    def test_persist_updates_existing_row(self, db_session):
        application = Application(status="COMPARED")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        first = run_determination([_comp("brand_name", "MATCH", form_value="X", label_value="X")])
        persist_determination(db_session, application, first)

        second = run_determination(
            [_comp("net_contents", "HARD_FAILURE", note="No Net Contents value found on any submitted label image.")]
        )
        persist_determination(db_session, application, second)

        rows = db_session.query(Determination).filter(Determination.application_id == application.id).all()
        assert len(rows) == 1
        assert rows[0].recommendation == "DENY"
        assert "net_contents" in rows[0].hard_failures_json

    def test_persist_serializes_hard_failures_and_allowable_revisions(self, db_session):
        application = Application(status="COMPARED")
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)

        comparisons = [
            _comp(
                "applicant_address",
                "POSSIBLE_ALLOWABLE",
                form_value="123 Main St, Lexington, KY",
                label_value="456 Oak Ave, Lexington, KY",
                section_v_ref="19",
                note="Address differs from the label, but both are in Kentucky (Sec. V item 19: change of name/address within the same state).",
            ),
        ]
        result = run_determination(comparisons)
        determination = persist_determination(db_session, application, result)

        assert determination.recommendation == "RECOMMEND_EXEMPTION_REVIEW"
        assert "19" in determination.allowable_json
        assert "Kentucky" in determination.allowable_json

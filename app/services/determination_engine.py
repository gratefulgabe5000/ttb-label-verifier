"""Stage 6: Determination & Reporting (WBS 8.0, FR-060-065, DevLog Section 3.2 Stage 6).

Takes the Stage 5 `comparisons` rows for one application and produces an overall
recommendation (8.1), the FR-063/064 hard-failure and allowable-revision lists (8.2),
a per-application determination report (8.3), and persistence to `determinations` (8.4).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.application import Application
from models.comparison import Comparison
from models.determination import Determination
from models.form_parameter import FormParameter
from models.label_parameter import LabelParameter

# Human-readable labels for field names, used when a HARD_FAILURE comparison has no
# `note` of its own (i.e. a plain text mismatch) and FR-063 still requires a
# plain-English description.
FIELD_LABELS = {
    "brand_name": "Brand Name",
    "government_warning": "Government Warning statement",
    "government_warning_text": "Government Warning -- statement text (27 CFR § 16.21)",
    "government_warning_caps": "Government Warning -- header in ALL CAPS",
    "government_warning_bold": "Government Warning -- header in bold type",
    "for_sale_in_state": 'Type 14b "for sale in [STATE]" statement',
    "country_of_origin": "Country of Origin",
    "fanciful_name": "Fanciful Name",
    "product_type": "Product/Class-Type designation",
    "applicant_name": "Applicant Name",
    "applicant_address": "Applicant Address",
    "grape_varietals": "Grape Varietals",
    "wine_appellation": "Wine Appellation",
    "alcohol_content": "Alcohol Content (ABV)",
    "net_contents": "Net Contents",
    "label_field_of_vision": "Brand Name / Class-Type / ABV -- same field of vision",
}


@dataclass
class HardFailureItem:
    """One DENY-list entry (FR-063): field name, form/label values, plain-English description."""

    field_name: str
    form_value: str | None
    label_value: str | None
    description: str


@dataclass
class AllowableRevisionItem:
    """One RECOMMEND_EXEMPTION_REVIEW-list entry (FR-064): field, discrepancy, Section V ref."""

    field_name: str
    discrepancy: str
    section_v_ref: str | None


@dataclass
class DeterminationResult:
    """8.1 + 8.2 output -- ready for persistence (8.4) or reporting (8.3)."""

    recommendation: str  # APPROVE | DENY | RECOMMEND_EXEMPTION_REVIEW
    hard_failures: list[HardFailureItem]
    allowable_revisions: list[AllowableRevisionItem]


@dataclass
class DeterminationReport:
    """8.3 -- per-application determination report (FR-065)."""

    application_id: int
    recommendation: str
    comparisons: list[Comparison]
    hard_failures: list[HardFailureItem]
    allowable_revisions: list[AllowableRevisionItem]
    confidence_scores: dict[str, float]
    processed_at: datetime


# ---------------------------------------------------------------------------
# 8.1 -- Determination logic (FR-060-062)
# ---------------------------------------------------------------------------


def determine_recommendation(comparisons: list[Comparison]) -> str:
    """APPROVE / DENY / RECOMMEND_EXEMPTION_REVIEW from the Stage 5 results.

    - DENY if any comparison is HARD_FAILURE (FR-061) -- takes precedence.
    - RECOMMEND_EXEMPTION_REVIEW if no HARD_FAILURE but one or more POSSIBLE_ALLOWABLE
      (FR-062).
    - APPROVE otherwise -- all comparisons MATCH, or there are none at all (FR-060).
    """
    if any(c.result == "HARD_FAILURE" for c in comparisons):
        return "DENY"
    if any(c.result == "POSSIBLE_ALLOWABLE" for c in comparisons):
        return "RECOMMEND_EXEMPTION_REVIEW"
    return "APPROVE"


# ---------------------------------------------------------------------------
# 8.2 -- Hard-failure / allowable-revision lists (FR-063, FR-064)
# ---------------------------------------------------------------------------


def _describe_hard_failure(comparison: Comparison) -> str:
    """Plain-English description (FR-063), falling back to a generated one when the
    comparison rule didn't already provide a `note` (i.e. a plain text mismatch)."""
    if comparison.note:
        return comparison.note
    label = FIELD_LABELS.get(comparison.field_name or "", comparison.field_name or "Field")
    form_value = comparison.form_value or "(blank)"
    label_value = comparison.label_value or "(not found on label)"
    return f'{label} on the form ("{form_value}") does not match the value found on the label ("{label_value}").'


def build_hard_failures(comparisons: list[Comparison]) -> list[HardFailureItem]:
    """FR-063: one entry per HARD_FAILURE comparison."""
    return [
        HardFailureItem(
            field_name=c.field_name,
            form_value=c.form_value,
            label_value=c.label_value,
            description=_describe_hard_failure(c),
        )
        for c in comparisons
        if c.result == "HARD_FAILURE"
    ]


def build_allowable_revisions(comparisons: list[Comparison]) -> list[AllowableRevisionItem]:
    """FR-064: one entry per POSSIBLE_ALLOWABLE comparison."""
    return [
        AllowableRevisionItem(
            field_name=c.field_name,
            discrepancy=c.note or "",
            section_v_ref=c.section_v_ref,
        )
        for c in comparisons
        if c.result == "POSSIBLE_ALLOWABLE"
    ]


def run_determination(comparisons: list[Comparison]) -> DeterminationResult:
    """8.1 + 8.2 -- the overall recommendation plus its supporting lists."""
    return DeterminationResult(
        recommendation=determine_recommendation(comparisons),
        hard_failures=build_hard_failures(comparisons),
        allowable_revisions=build_allowable_revisions(comparisons),
    )


# ---------------------------------------------------------------------------
# 8.3 -- Determination report (FR-065)
# ---------------------------------------------------------------------------


def build_confidence_scores(
    form_parameters: list[FormParameter], label_parameters: list[LabelParameter]
) -> dict[str, float]:
    """Per-field extraction confidence (FR-065): Stage 4 (label) values as a base,
    overridden by Stage 3 (form) values where the field was extracted from the form."""
    scores: dict[str, float] = {}
    for lp in label_parameters:
        if lp.field_value and lp.confidence is not None:
            scores[lp.field_name] = max(scores.get(lp.field_name, 0.0), lp.confidence)
    for fp in form_parameters:
        if fp.field_value and fp.confidence is not None:
            scores[fp.field_name] = fp.confidence
    return scores


def build_determination_report(
    application: Application,
    comparisons: list[Comparison],
    form_parameters: list[FormParameter],
    label_parameters: list[LabelParameter],
    result: DeterminationResult,
    processed_at: datetime,
) -> DeterminationReport:
    """FR-065: all comparison results, the overall determination, confidence scores,
    and the processing timestamp -- plus the FR-063/064 lists from `result`."""
    return DeterminationReport(
        application_id=application.id,
        recommendation=result.recommendation,
        comparisons=comparisons,
        hard_failures=result.hard_failures,
        allowable_revisions=result.allowable_revisions,
        confidence_scores=build_confidence_scores(form_parameters, label_parameters),
        processed_at=processed_at,
    )


# ---------------------------------------------------------------------------
# 8.4 -- Persistence (DevLog Section 3.4)
# ---------------------------------------------------------------------------


def persist_determination(db: Session, application: Application, result: DeterminationResult) -> Determination:
    """Upsert the `determinations` row for `application` and mark it processed."""
    determination = db.query(Determination).filter(Determination.application_id == application.id).first()
    if determination is None:
        determination = Determination(application_id=application.id)
        db.add(determination)

    determination.recommendation = result.recommendation
    determination.hard_failures_json = json.dumps([asdict(item) for item in result.hard_failures])
    determination.allowable_json = json.dumps([asdict(item) for item in result.allowable_revisions])
    # A re-run of Stage 5/6 (process/reprocess) recomputes the determination, so any
    # prior finalization (FR-090) no longer applies -- the agent must finalize again.
    determination.finalized_at = None

    application.status = "DETERMINED"
    application.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(determination)
    db.refresh(application)
    return determination

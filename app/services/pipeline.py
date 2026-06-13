"""Stage 3-6 single-application pipeline orchestration (WBS 9.1, FR-074).

Extends the per-image concurrent-compute / sequential-persist pattern (IA-24,
already used inside Stage 4 -- `label_extraction.run_stage4_extraction`) to the
whole pipeline: Stage 3 (form) and Stage 4 (label) extraction run concurrently,
their results are persisted, and Stage 5 (comparison) and Stage 6
(determination) then run against the persisted results.
"""

from __future__ import annotations

import asyncio

from anthropic import Anthropic
from sqlalchemy.orm import Session

from models.application import Application
from models.form_parameter import FormParameter
from models.label_image import LabelImage
from models.label_parameter import LabelParameter
from services import application_service, comparison_engine, determination_engine, form_extraction, label_extraction
from services.comparison_engine import US_STATES, _extract_state


async def run_extraction(
    application: Application, label_images: list[LabelImage], *, client: Anthropic | None = None
) -> tuple[dict, dict]:
    """Stage 3 + Stage 4 extraction, run concurrently (IA-24)."""
    return await asyncio.gather(
        asyncio.to_thread(form_extraction.run_stage3_extraction, application.form_path, client=client),
        label_extraction.run_stage4_extraction(label_images, client=client),
    )


def _resolve_label_field(label_parameters: list[LabelParameter], field_name: str) -> str | None:
    """Highest-confidence non-empty value for `field_name` across label images (IA-18)."""
    candidates = [lp for lp in label_parameters if lp.field_name == field_name and lp.field_value]
    if not candidates:
        return None
    return max(candidates, key=lambda lp: lp.confidence or 0.0).field_value


def _update_registry_fields(
    application: Application, form_parameters: list[FormParameter], label_parameters: list[LabelParameter]
) -> None:
    """Populate the COLA Public Registry display fields (`class_type_code`,
    `origin_code`) as soon as Stage 3/4 results are available -- even before the
    determination is finalized."""
    class_type = _resolve_label_field(label_parameters, "class_type_designation")
    if class_type:
        application.class_type_code = class_type

    if application.source == "imported":
        country = _resolve_label_field(label_parameters, "country_of_origin")
        if country:
            application.origin_code = country
    elif application.source == "domestic":
        applicant_address = next(
            (fp.field_value for fp in form_parameters if fp.field_name == "applicant_address" and fp.field_value),
            None,
        )
        state_code = _extract_state(applicant_address)
        if state_code:
            application.origin_code = US_STATES.get(state_code, state_code)


def run_stages_5_6(db: Session, application: Application) -> Application:
    """Run + persist Stage 5 (comparison) and Stage 6 (determination) against
    whatever Stage 3/4 results are currently persisted for `application`."""
    form_parameters = application_service.list_form_parameters(db, application.id)
    label_parameters = application_service.list_label_parameters(db, application.id)

    _update_registry_fields(application, form_parameters, label_parameters)

    comparisons = comparison_engine.run_comparisons(form_parameters, application, label_parameters)
    comparison_engine.persist_comparisons(db, application, comparisons)

    persisted_comparisons = application_service.list_comparisons(db, application.id)
    result = determination_engine.run_determination(persisted_comparisons)
    determination_engine.persist_determination(db, application, result)

    db.refresh(application)
    return application


def persist_extraction_and_run_stages_5_6(
    db: Session, application: Application, form_results: dict, label_results: dict
) -> Application:
    """Persist Stage 3/4 results (IA-24), then run + persist Stage 5 and Stage 6."""
    form_extraction.persist_form_parameters(db, application, form_results)
    label_extraction.persist_label_parameters(db, application, label_results)
    return run_stages_5_6(db, application)


async def process_application(db: Session, application: Application, *, client: Anthropic | None = None) -> Application:
    """9.1: run Stages 3-6 for one application, reaching a terminal status (FR-074)."""
    application.status = "PROCESSING"
    db.commit()

    label_images = application_service.list_label_images(db, application.id)
    try:
        form_results, label_results = await run_extraction(application, label_images, client=client)
    except Exception:
        application.status = "ERROR"
        db.commit()
        db.refresh(application)
        return application

    return persist_extraction_and_run_stages_5_6(db, application, form_results, label_results)


async def reprocess_form(db: Session, application: Application, *, client: Anthropic | None = None) -> Application:
    """Re-run Stage 3 (form extraction) only, then refresh Stage 5/6 against the
    existing Stage 4 (label) results."""
    application.status = "PROCESSING"
    db.commit()

    try:
        form_results = await asyncio.to_thread(form_extraction.run_stage3_extraction, application.form_path, client=client)
    except Exception:
        application.status = "ERROR"
        db.commit()
        db.refresh(application)
        return application

    form_extraction.persist_form_parameters(db, application, form_results)
    return run_stages_5_6(db, application)


async def reprocess_label(
    db: Session, application: Application, label_images: list[LabelImage], *, client: Anthropic | None = None
) -> Application:
    """Re-run Stage 4 (label extraction) only, then refresh Stage 5/6 against the
    existing Stage 3 (form) results."""
    application.status = "PROCESSING"
    db.commit()

    try:
        label_results = await label_extraction.run_stage4_extraction(label_images, client=client)
    except Exception:
        application.status = "ERROR"
        db.commit()
        db.refresh(application)
        return application

    label_extraction.persist_label_parameters(db, application, label_results)
    return run_stages_5_6(db, application)


def reprocess_comparison(db: Session, application: Application) -> Application:
    """Re-run Stage 5/6 (comparison + determination) against the existing Stage
    3/4 results, without re-running extraction."""
    return run_stages_5_6(db, application)

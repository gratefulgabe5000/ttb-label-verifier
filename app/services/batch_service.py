"""Batch Orchestrator (WBS 9.3-9.5): bounded-concurrency Stage 3-6 processing
across a set of applications, plus batch summary persistence and status (A-07,
IA-17, FR-074-077).

Extends the pipeline's concurrent-compute / sequential-persist pattern (IA-24,
`services.pipeline`) to the batch level: Stage 3/4 extraction for each
application runs concurrently, bounded by a semaphore (3-5 in flight per A-07),
while Stage 3-6 persistence happens sequentially, one application at a time, as
each application's extraction resolves -- in completion order, which may differ
from the batch's selection order (A-07).
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from anthropic import Anthropic
from sqlalchemy.orm import Session

from models.application import Application
from models.batch import Batch
from models.comparison import Comparison
from models.determination import Determination
from services import application_service, pipeline, settings_service
from services.determination_engine import FIELD_LABELS

DEFAULT_BATCH_CONCURRENCY = 4

# Terminal application statuses for the purposes of batch progress (FR-075).
TERMINAL_STATUSES = ("DETERMINED", "FINALIZED", "ERROR")

RECOMMENDATION_COUNT_FIELDS = {
    "APPROVE": "approved_count",
    "DENY": "denied_count",
    "RECOMMEND_EXEMPTION_REVIEW": "exemption_count",
}


def create_batch(db: Session, *, application_ids: list[int], created_by: int) -> Batch:
    """9.4: insert a `batches` row for the given application IDs."""
    batch = Batch(application_ids=json.dumps(application_ids), created_by=created_by)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


async def run_batch(
    db: Session, batch: Batch, applications: list[Application], *, concurrency: int = DEFAULT_BATCH_CONCURRENCY
) -> None:
    """9.3: process every application in `applications`, bounded by a semaphore (A-07/IA-17)."""
    client = Anthropic() if settings_service.is_configured() else None
    semaphore = asyncio.Semaphore(concurrency)

    for application in applications:
        application.status = "PROCESSING"
    db.commit()

    async def _compute(application: Application) -> tuple[Application, dict | None, dict | None]:
        async with semaphore:
            label_images = application_service.list_label_images(db, application.id)
            try:
                form_results, label_results = await pipeline.run_extraction(application, label_images, client=client)
            except Exception:
                return application, None, None
            return application, form_results, label_results

    tasks = [asyncio.create_task(_compute(application)) for application in applications]
    for task in asyncio.as_completed(tasks):
        application, form_results, label_results = await task
        if form_results is None:
            application.status = "ERROR"
            db.commit()
            continue
        pipeline.persist_extraction_and_run_stages_5_6(db, application, form_results, label_results)

    _finalize_batch(db, batch, applications)


def _finalize_batch(db: Session, batch: Batch, applications: list[Application]) -> None:
    """FR-077: compute and persist the batch summary counts."""
    counts = {field: 0 for field in RECOMMENDATION_COUNT_FIELDS}
    for application in applications:
        determination = db.query(Determination).filter(Determination.application_id == application.id).first()
        if determination and determination.recommendation in RECOMMENDATION_COUNT_FIELDS:
            counts[determination.recommendation] += 1

    batch.approved_count = counts["APPROVE"]
    batch.denied_count = counts["DENY"]
    batch.exemption_count = counts["RECOMMEND_EXEMPTION_REVIEW"]
    batch.summary_json = json.dumps(counts)
    batch.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


def get_batch_status(db: Session, batch: Batch) -> dict:
    """9.5: current per-application status and overall progress (FR-075, FR-076)."""
    application_ids: list[int] = json.loads(batch.application_ids or "[]")
    applications_by_id = {
        application.id: application
        for application in db.query(Application).filter(Application.id.in_(application_ids)).all()
    }

    total = len(application_ids)
    completed = 0
    counts = {field: 0 for field in RECOMMENDATION_COUNT_FIELDS}
    application_statuses = []

    for application_id in application_ids:
        application = applications_by_id.get(application_id)
        if application is None:
            continue

        recommendation = None
        if application.status in TERMINAL_STATUSES:
            completed += 1
            determination = (
                db.query(Determination).filter(Determination.application_id == application_id).first()
            )
            if determination:
                recommendation = determination.recommendation
                if recommendation in counts:
                    counts[recommendation] += 1

        application_statuses.append({"id": application_id, "status": application.status, "recommendation": recommendation})

    return {
        "id": batch.id,
        "status": "COMPLETE" if completed == total else "PROCESSING",
        "total": total,
        "completed": completed,
        "approved_count": counts["APPROVE"],
        "denied_count": counts["DENY"],
        "exemption_count": counts["RECOMMEND_EXEMPTION_REVIEW"],
        "applications": application_statuses,
        "created_at": batch.created_at,
        "completed_at": batch.completed_at,
    }


def get_batch_report(db: Session, batch: Batch) -> dict:
    """10.3: FR-095-097 batch report -- status summary plus the most common failure type."""
    application_ids: list[int] = json.loads(batch.application_ids or "[]")

    failure_counts: dict[str, int] = {}
    for comparison in (
        db.query(Comparison)
        .filter(Comparison.application_id.in_(application_ids), Comparison.result == "HARD_FAILURE")
        .all()
    ):
        label = FIELD_LABELS.get(comparison.field_name or "", comparison.field_name or "Field")
        failure_counts[label] = failure_counts.get(label, 0) + 1

    most_common_failure = max(failure_counts, key=failure_counts.get) if failure_counts else None

    return {**get_batch_status(db, batch), "most_common_failure": most_common_failure}

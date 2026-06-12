"""Agent overrides and finalization (WBS 10.1-10.2, FR-086-090, SR-004, A-15)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.application import Application
from models.comparison import Comparison
from models.determination import Determination


class FieldNotFoundError(LookupError):
    """Raised when an override's `field` does not match any comparison for the application."""


def apply_override(
    db: Session, determination: Determination, *, agent_id: int, field: str | None, override_value: str, reason: str
) -> tuple[str | None, datetime]:
    """FR-086-089/SR-004: record an agent override, returning (original_value, override_at).

    `field` is None for an overall-determination override (FR-089), persisted on
    `determinations`; otherwise it names a `comparisons.field_name` for a
    per-parameter override (FR-086-088), persisted on that `comparisons` row. In
    both cases the original AI value is left untouched and the override is recorded
    alongside it (FR-088).
    """
    override_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if field is None:
        original_value = determination.recommendation
        determination.agent_override = override_value
        determination.override_by = agent_id
        determination.override_reason = reason
        determination.override_at = override_at
    else:
        comparison = (
            db.query(Comparison)
            .filter(Comparison.application_id == determination.application_id, Comparison.field_name == field)
            .first()
        )
        if comparison is None:
            raise FieldNotFoundError(field)

        original_value = comparison.result
        comparison.agent_override = override_value
        comparison.override_by = agent_id
        comparison.override_reason = reason
        comparison.override_at = override_at

    db.commit()
    return original_value, override_at


def finalize_determination(db: Session, determination: Determination) -> Determination:
    """FR-090/A-15: commit the determination as final; does not re-run the AI pipeline."""
    determination.finalized_at = datetime.now(timezone.utc).replace(tzinfo=None)

    application = db.get(Application, determination.application_id)
    if application is not None:
        application.status = "FINALIZED"

    db.commit()
    db.refresh(determination)
    return determination

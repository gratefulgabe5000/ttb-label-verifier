"""Agent override & finalization endpoints (WBS 10.1-10.2, DevLog §3.5, FR-086-090)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dependencies import get_current_agent
from models.agent import Agent
from models.application import Application
from models.determination import Determination
from schemas.application import DeterminationOut
from schemas.determination import OverrideIn, OverrideOut
from services import override_service

router = APIRouter(prefix="/determinations", tags=["determinations"], dependencies=[Depends(get_current_agent)])


def _get_owned_determination(db: Session, determination_id: int, agent: Agent) -> Determination:
    determination = db.get(Determination, determination_id)
    if determination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Determination not found.")

    application = db.get(Application, determination.application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Determination not found.")

    return determination


@router.post("/{determination_id}/override", response_model=OverrideOut)
def override_determination(
    determination_id: int,
    payload: OverrideIn,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> OverrideOut:
    """FR-086-089/SR-004: per-parameter (`field` set) or overall (`field` omitted) override."""
    determination = _get_owned_determination(db, determination_id, agent)

    try:
        original_value, override_at = override_service.apply_override(
            db,
            determination,
            agent_id=agent.id,
            field=payload.field,
            override_value=payload.override_value,
            reason=payload.reason,
        )
    except override_service.FieldNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No comparison found for field '{exc}'."
        ) from exc

    return OverrideOut(
        application_id=determination.application_id,
        field=payload.field,
        original_value=original_value,
        override_value=payload.override_value,
        override_by=agent.id,
        override_reason=payload.reason,
        override_at=override_at,
    )


@router.post("/{determination_id}/finalize", response_model=DeterminationOut)
def finalize(
    determination_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> Determination:
    """FR-090/A-15: commit the determination as final; does not re-run the AI pipeline."""
    determination = _get_owned_determination(db, determination_id, agent)
    return override_service.finalize_determination(db, determination)

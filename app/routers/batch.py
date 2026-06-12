"""Batch processing endpoints (WBS 9.4/9.5, DevLog §3.5, FR-074-077)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dependencies import get_current_agent
from models.agent import Agent
from models.application import Application
from models.batch import Batch
from schemas.batch import BatchProcessIn, BatchStatusOut
from services import batch_service

router = APIRouter(prefix="/batch", tags=["batch"], dependencies=[Depends(get_current_agent)])


@router.post("/process", response_model=BatchStatusOut, status_code=status.HTTP_201_CREATED)
async def process_batch(
    payload: BatchProcessIn,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BatchStatusOut:
    """FR-074: run the Stage 3-6 pipeline for every selected application (A-07 bounded concurrency)."""
    applications = (
        db.query(Application)
        .filter(Application.id.in_(payload.application_ids), Application.assigned_agent_id == agent.id)
        .all()
    )
    if len(applications) != len(set(payload.application_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more applications not found.")

    batch = batch_service.create_batch(db, application_ids=payload.application_ids, created_by=agent.id)
    await batch_service.run_batch(db, batch, applications)

    return BatchStatusOut(**batch_service.get_batch_status(db, batch))


@router.get("/{batch_id}/status", response_model=BatchStatusOut)
def get_status(
    batch_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BatchStatusOut:
    """FR-075: poll for batch progress ('X of N complete') and per-application badges."""
    batch = db.get(Batch, batch_id)
    if batch is None or batch.created_by != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")

    return BatchStatusOut(**batch_service.get_batch_status(db, batch))

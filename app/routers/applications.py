"""Application ingestion endpoints (DevLog Stages 1-2, §3.5 API surface)."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db import get_db
from dependencies import get_current_agent
from models.agent import Agent
from models.application import Application
from models.comparison import Comparison
from models.determination import Determination
from models.label_image import LabelImage
from schemas.application import (
    ApplicationDetailOut,
    ApplicationOut,
    ComparisonOut,
    DeterminationOut,
    FormParameterOut,
    LabelImageOut,
    LabelParameterOut,
)
from services import application_service, pipeline
from services.application_service import FileValidationError

router = APIRouter(prefix="/applications", tags=["applications"], dependencies=[Depends(get_current_agent)])


def _application_out(application: Application, determination: Determination | None) -> ApplicationOut:
    """Surface the effective recommendation/finalization (FR-090) on the application."""
    recommendation = None
    finalized_at = None
    if determination:
        recommendation = determination.agent_override or determination.recommendation
        finalized_at = determination.finalized_at

    base = ApplicationOut.model_validate(application).model_dump(exclude={"recommendation", "finalized_at"})
    return ApplicationOut(**base, recommendation=recommendation, finalized_at=finalized_at)


def _to_detail(db: Session, application: Application) -> ApplicationDetailOut:
    label_images = application_service.list_label_images(db, application.id)
    form_parameters = application_service.list_form_parameters(db, application.id)
    label_parameters = application_service.list_label_parameters(db, application.id)
    determination = application_service.get_determination(db, application.id)
    return ApplicationDetailOut(
        **_application_out(application, determination).model_dump(),
        label_images=[LabelImageOut.model_validate(image) for image in label_images],
        form_parameters=[FormParameterOut.model_validate(param) for param in form_parameters],
        label_parameters=[LabelParameterOut.model_validate(param) for param in label_parameters],
        determination=DeterminationOut.model_validate(determination) if determination else None,
    )


@router.post("/upload", response_model=ApplicationDetailOut, status_code=status.HTTP_201_CREATED)
async def upload_application(
    form_file: UploadFile = File(...),
    label_images: list[UploadFile] = File(default=[]),
    label_types: list[str] = Form(default=[]),
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    """One application per call (FR-001-006); call repeatedly for batch ingestion (FR-006)."""
    form_content = await form_file.read()
    try:
        application_service.validate_form_file(form_file.filename or "form.pdf", form_content)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    label_files: list[tuple[str, bytes, str | None]] = []
    for index, image in enumerate(label_images):
        content = await image.read()
        filename = image.filename or f"label_{index + 1}"
        try:
            application_service.validate_label_image(filename, content)
        except FileValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        label_type = label_types[index] if index < len(label_types) else None
        label_files.append((filename, content, label_type))

    application = application_service.create_application(
        db,
        agent_id=agent.id,
        form_filename=form_file.filename or "form.pdf",
        form_content=form_content,
        label_files=label_files,
    )
    await pipeline.process_new_upload(db, application)
    return _to_detail(db, application)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_applications(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> None:
    """Settings 'Danger Zone' -- remove all of this agent's applications, their
    cascade-related rows, and uploaded files, to reset test data."""
    application_service.delete_all_applications(db, agent.id)


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> list[ApplicationOut]:
    """FR-070 (own applications only, SR-002)."""
    applications = (
        db.query(Application)
        .filter(Application.assigned_agent_id == agent.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    if not applications:
        return []

    determinations = {
        determination.application_id: determination
        for determination in db.query(Determination)
        .filter(Determination.application_id.in_([application.id for application in applications]))
        .all()
    }
    return [_application_out(application, determinations.get(application.id)) for application in applications]


@router.get("/{application_id}", response_model=ApplicationDetailOut)
def get_application(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    return _to_detail(db, application)


@router.get("/{application_id}/form")
def get_application_form(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Serve the uploaded application form PDF (13.2 — react-pdf renderer)."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    if not application.form_path or not Path(application.form_path).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form file not found.")

    return FileResponse(application.form_path, media_type="application/pdf")


@router.get("/{application_id}/label-images/{image_id}")
def get_application_label_image(
    application_id: int,
    image_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Serve an uploaded label image (13.3 — multi-image tab selector)."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    label_image = db.get(LabelImage, image_id)
    if label_image is None or label_image.application_id != application_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label image not found.")

    if not Path(label_image.image_path).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label image file not found.")

    return FileResponse(label_image.image_path)


# ---------------------------------------------------------------------------
# 9.2 -- Pipeline orchestration (FR-074)
# ---------------------------------------------------------------------------


@router.post("/{application_id}/process", response_model=ApplicationDetailOut)
async def process_application(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    """Run the full Stage 3-6 pipeline for one application (9.1, FR-074)."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    await pipeline.process_application(db, application)
    return _to_detail(db, application)


# ---------------------------------------------------------------------------
# Per-stage reprocessing (Detail View "Reprocess" actions)
# ---------------------------------------------------------------------------


@router.post("/{application_id}/reprocess/form", response_model=ApplicationDetailOut)
async def reprocess_form(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    """Re-run Stage 3 (form assessment) only, then refresh Stage 5/6."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    await pipeline.reprocess_form(db, application)
    return _to_detail(db, application)


@router.post("/{application_id}/reprocess/label", response_model=ApplicationDetailOut)
async def reprocess_label(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    """Re-run Stage 4 (label assessment) only, then refresh Stage 5/6."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    label_images = application_service.list_label_images(db, application.id)
    await pipeline.reprocess_label(db, application, label_images)
    return _to_detail(db, application)


@router.post("/{application_id}/reprocess/comparison", response_model=ApplicationDetailOut)
def reprocess_comparison(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ApplicationDetailOut:
    """Re-run Stage 5/6 (comparison + determination) against existing Stage 3/4 results."""
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    pipeline.reprocess_comparison(db, application)
    return _to_detail(db, application)


# ---------------------------------------------------------------------------
# 9.6 -- Comparison results (DevLog §3.5)
# ---------------------------------------------------------------------------


@router.get("/{application_id}/comparisons", response_model=list[ComparisonOut])
def get_application_comparisons(
    application_id: int,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> list[Comparison]:
    application = db.get(Application, application_id)
    if application is None or application.assigned_agent_id != agent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    return application_service.list_comparisons(db, application.id)

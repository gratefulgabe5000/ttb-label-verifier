"""Application ingestion endpoints (DevLog Stages 1-2, §3.5 API surface)."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db import get_db
from dependencies import get_current_agent
from models.agent import Agent
from models.application import Application
from models.label_image import LabelImage
from schemas.application import (
    ApplicationDetailOut,
    ApplicationOut,
    DeterminationOut,
    FormParameterOut,
    LabelImageOut,
    LabelParameterOut,
)
from services import application_service
from services.application_service import FileValidationError

router = APIRouter(prefix="/applications", tags=["applications"], dependencies=[Depends(get_current_agent)])


def _to_detail(db: Session, application: Application) -> ApplicationDetailOut:
    label_images = application_service.list_label_images(db, application.id)
    form_parameters = application_service.list_form_parameters(db, application.id)
    label_parameters = application_service.list_label_parameters(db, application.id)
    determination = application_service.get_determination(db, application.id)
    return ApplicationDetailOut(
        **ApplicationOut.model_validate(application).model_dump(),
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
    serial_number: str | None = Form(default=None),
    applicant_name: str | None = Form(default=None),
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
        serial_number=serial_number,
        applicant_name=applicant_name,
    )
    return _to_detail(db, application)


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    applicant_name: str | None = Query(default=None),
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> list[Application]:
    """FR-070 (own applications only, SR-002), FR-072 (filter by applicant name)."""
    query = db.query(Application).filter(Application.assigned_agent_id == agent.id)
    if applicant_name:
        query = query.filter(Application.applicant_name.ilike(f"%{applicant_name}%"))
    return query.order_by(Application.created_at.desc()).all()


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

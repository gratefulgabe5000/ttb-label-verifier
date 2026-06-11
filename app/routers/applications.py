"""Application ingestion endpoints (DevLog Stages 1-2, §3.5 API surface)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from db import get_db
from dependencies import get_current_agent
from models.agent import Agent
from models.application import Application
from schemas.application import ApplicationDetailOut, ApplicationOut, LabelImageOut
from services import application_service
from services.application_service import FileValidationError

router = APIRouter(prefix="/applications", tags=["applications"], dependencies=[Depends(get_current_agent)])


def _to_detail(db: Session, application: Application) -> ApplicationDetailOut:
    label_images = application_service.list_label_images(db, application.id)
    return ApplicationDetailOut(
        **ApplicationOut.model_validate(application).model_dump(),
        label_images=[LabelImageOut.model_validate(image) for image in label_images],
        form_parameters=[],
        label_parameters=[],
        determination=None,
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

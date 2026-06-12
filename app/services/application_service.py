"""Application ingestion: file validation and persistence (DevLog Stages 1-2)."""

from pathlib import Path

from sqlalchemy.orm import Session

from config import get_settings
from models.application import Application
from models.determination import Determination
from models.form_parameter import FormParameter
from models.label_image import LabelImage
from models.label_parameter import LabelParameter

settings = get_settings()

# IR-002 / IR-003
MAX_FORM_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

_PDF_MAGIC = b"%PDF"
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class FileValidationError(ValueError):
    """Raised when an uploaded file fails the FR-001/002/007 or IR-002/003 checks."""


def _is_webp(content: bytes) -> bool:
    return content[:4] == b"RIFF" and content[8:12] == b"WEBP"


def validate_form_file(filename: str, content: bytes) -> None:
    """FR-001 (PDF), FR-007 (rejection message), IR-002 (20 MB limit)."""
    if len(content) > MAX_FORM_SIZE_BYTES:
        raise FileValidationError(f"'{filename}' exceeds the 20 MB size limit for application forms.")
    if not content.startswith(_PDF_MAGIC):
        raise FileValidationError(
            f"'{filename}' is not a valid PDF. Application forms must be submitted as a PDF file."
        )


def validate_label_image(filename: str, content: bytes) -> None:
    """FR-002 (JPEG/PNG/WebP), FR-007 (rejection message), IR-003 (10 MB limit)."""
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise FileValidationError(f"'{filename}' exceeds the 10 MB size limit for label images.")
    if not (content.startswith(_JPEG_MAGIC) or content.startswith(_PNG_MAGIC) or _is_webp(content)):
        raise FileValidationError(f"'{filename}' is not a valid JPEG, PNG, or WebP image.")


def _extension(filename: str, fallback: str) -> str:
    suffix = Path(filename).suffix
    return suffix if suffix else fallback


def create_application(
    db: Session,
    *,
    agent_id: int,
    form_filename: str,
    form_content: bytes,
    label_files: list[tuple[str, bytes, str | None]],
    serial_number: str | None,
    applicant_name: str | None,
) -> Application:
    """Insert the `applications` row and any `label_images` rows, persisting files to disk."""
    application = Application(
        serial_number=serial_number,
        applicant_name=applicant_name,
        assigned_agent_id=agent_id,
        status="PENDING",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    app_dir = Path(settings.upload_dir) / str(application.id)
    app_dir.mkdir(parents=True, exist_ok=True)

    form_path = app_dir / f"form{_extension(form_filename, '.pdf')}"
    form_path.write_bytes(form_content)
    application.form_path = str(form_path)

    for index, (filename, content, label_type) in enumerate(label_files, start=1):
        image_path = app_dir / f"label_{index}{_extension(filename, '.jpg')}"
        image_path.write_bytes(content)
        db.add(LabelImage(application_id=application.id, image_path=str(image_path), label_type=label_type))

    db.commit()
    db.refresh(application)
    return application


def list_label_images(db: Session, application_id: int) -> list[LabelImage]:
    return (
        db.query(LabelImage)
        .filter(LabelImage.application_id == application_id)
        .order_by(LabelImage.id)
        .all()
    )


def list_form_parameters(db: Session, application_id: int) -> list[FormParameter]:
    return (
        db.query(FormParameter)
        .filter(FormParameter.application_id == application_id)
        .order_by(FormParameter.id)
        .all()
    )


def list_label_parameters(db: Session, application_id: int) -> list[LabelParameter]:
    return (
        db.query(LabelParameter)
        .filter(LabelParameter.application_id == application_id)
        .order_by(LabelParameter.id)
        .all()
    )


def get_determination(db: Session, application_id: int) -> Determination | None:
    return db.query(Determination).filter(Determination.application_id == application_id).first()

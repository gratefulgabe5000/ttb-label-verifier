from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class LabelParameter(Base):
    """One extracted field from a single label image (FR-030–040)."""

    __tablename__ = "label_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    label_image_id: Mapped[int | None] = mapped_column(ForeignKey("label_images.id"))
    field_name: Mapped[str | None] = mapped_column(String)
    field_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    location_hint: Mapped[str | None] = mapped_column(String)  # fallback annotation position (IA-13)
    bbox_json: Mapped[str | None] = mapped_column(Text)  # OCR fuzzy-match bbox (TS-02/IA-13/IA-21)
    # government_warning only: OCR text-height ratio corroborating header_caps_bold (TS-02 #3, IA-07)
    header_height_ratio: Mapped[float | None] = mapped_column(Float)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

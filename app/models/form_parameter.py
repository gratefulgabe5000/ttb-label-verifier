from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class FormParameter(Base):
    """One extracted field from TTB Form F 5100.31 Part I (FR-010–019)."""

    __tablename__ = "form_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    field_name: Mapped[str | None] = mapped_column(String)
    field_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    extraction_method: Mapped[str | None] = mapped_column(String)  # acroform|pdftext|ai_vision (TS-01/IA-20)
    location_hint: Mapped[str | None] = mapped_column(String)  # fallback annotation position (IA-13/IA-23)
    bbox_json: Mapped[str | None] = mapped_column(Text)  # {"x":..,"y":..,"w":..,"h":..} (FR-019/IA-23)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

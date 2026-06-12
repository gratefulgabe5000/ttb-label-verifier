from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Comparison(Base):
    """One per-field form-vs-label comparison result (FR-050–059, FR-066, FR-100–107)."""

    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    field_name: Mapped[str | None] = mapped_column(String)
    form_value: Mapped[str | None] = mapped_column(Text)
    label_value: Mapped[str | None] = mapped_column(Text)
    # MATCH|HARD_FAILURE|POSSIBLE_ALLOWABLE|MISSING_FROM_LABEL|MISSING_FROM_FORM (FR-058)
    result: Mapped[str | None] = mapped_column(String)
    section_v_ref: Mapped[str | None] = mapped_column(String)  # e.g. "3b" (FR-059)
    note: Mapped[str | None] = mapped_column(Text)
    # Label image the label_value was resolved from, for annotation placement (FR-038, WBS 7.1/13.5)
    label_image_id: Mapped[int | None] = mapped_column(ForeignKey("label_images.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class LabelImage(Base):
    """One label artwork image associated with an application (FR-003/FR-030)."""

    __tablename__ = "label_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    image_path: Mapped[str | None] = mapped_column(String)
    label_type: Mapped[str | None] = mapped_column(String)  # brand|back|neck|other
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

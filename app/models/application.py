from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Application(Base):
    """One TTB Form F 5100.31 submission and its associated label images."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    permit_no: Mapped[str | None] = mapped_column(String)  # Item 2 (plant_registry_number)
    serial_number: Mapped[str | None] = mapped_column(String)
    year: Mapped[str | None] = mapped_column(String)
    form_path: Mapped[str | None] = mapped_column(String)
    product_type: Mapped[str | None] = mapped_column(String)  # wine|distilled_spirits|malt_beverages
    source: Mapped[str | None] = mapped_column(String)  # domestic|imported
    brand_name: Mapped[str | None] = mapped_column(String)
    fanciful_name: Mapped[str | None] = mapped_column(String)  # Item 7
    applicant_name: Mapped[str | None] = mapped_column(String)
    application_type: Mapped[str | None] = mapped_column(String)  # 14a|14b|14c|14d
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    status: Mapped[str] = mapped_column(String, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # COLA Public Registry forward-compatibility fields (PRD FR-018, DevLog §6, IA-22) —
    # populated when derivable from the submitted form/label; no live registry connection.
    ttb_id: Mapped[str | None] = mapped_column(String)
    vendor_code: Mapped[str | None] = mapped_column(String)
    class_type_code: Mapped[str | None] = mapped_column(String)
    origin_code: Mapped[str | None] = mapped_column(String)
    registry_status: Mapped[str | None] = mapped_column(String)
    total_bottle_capacity: Mapped[str | None] = mapped_column(String)
    for_sale_in_state: Mapped[str | None] = mapped_column(String)
    qualifications: Mapped[str | None] = mapped_column(String)

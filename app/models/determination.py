from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Determination(Base):
    """The overall recommendation for one application, plus any agent override (FR-060–065, FR-086–090)."""

    __tablename__ = "determinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    recommendation: Mapped[str | None] = mapped_column(String)  # APPROVE|DENY|RECOMMEND_EXEMPTION_REVIEW
    hard_failures_json: Mapped[str | None] = mapped_column(Text)
    allowable_json: Mapped[str | None] = mapped_column(Text)
    agent_override: Mapped[str | None] = mapped_column(String)  # null|APPROVE|DENY|RECOMMEND_EXEMPTION_REVIEW
    override_by: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    override_reason: Mapped[str | None] = mapped_column(Text)
    override_at: Mapped[datetime | None] = mapped_column(DateTime)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

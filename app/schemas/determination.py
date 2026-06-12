from datetime import datetime

from pydantic import BaseModel, field_validator


class OverrideIn(BaseModel):
    """10.1 -- POST /determinations/{id}/override (DevLog §3.5)."""

    field: str | None = None  # None => overall determination override (FR-089); else per-parameter (FR-086-088)
    override_value: str
    reason: str

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be empty")  # FR-087
        return value


class OverrideOut(BaseModel):
    """FR-088/SR-004 audit trail: agent, original value, override value, reason, timestamp."""

    application_id: int
    field: str | None
    original_value: str | None
    override_value: str
    override_by: int
    override_reason: str
    override_at: datetime

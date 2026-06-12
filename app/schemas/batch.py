from datetime import datetime

from pydantic import BaseModel


class BatchProcessIn(BaseModel):
    """9.4 -- `POST /batch/process` request body."""

    application_ids: list[int]


class BatchApplicationStatusOut(BaseModel):
    """One application's row within a batch status response (FR-076)."""

    id: int
    status: str
    recommendation: str | None = None


class BatchStatusOut(BaseModel):
    """9.5 -- `GET /batch/{id}/status` response (FR-075, FR-077)."""

    id: int
    status: str  # PROCESSING | COMPLETE
    total: int
    completed: int
    approved_count: int
    denied_count: int
    exemption_count: int
    applications: list[BatchApplicationStatusOut]
    created_at: datetime
    completed_at: datetime | None


class BatchReportOut(BatchStatusOut):
    """10.3 -- `GET /batch/{id}/report` response (FR-095-097)."""

    most_common_failure: str | None = None

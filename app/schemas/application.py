from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LabelImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    image_path: str | None
    label_type: str | None
    uploaded_at: datetime


class FormParameterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    field_name: str | None
    field_value: str | None
    confidence: float | None
    extraction_method: str | None
    location_hint: str | None
    bbox_json: str | None
    extracted_at: datetime


class LabelParameterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    label_image_id: int | None
    field_name: str | None
    field_value: str | None
    confidence: float | None
    location_hint: str | None
    bbox_json: str | None
    header_height_ratio: float | None
    extracted_at: datetime


class DeterminationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    recommendation: str | None
    hard_failures_json: str | None
    allowable_json: str | None
    agent_override: str | None
    override_by: int | None
    override_reason: str | None
    override_at: datetime | None
    finalized_at: datetime | None
    created_at: datetime


class ComparisonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    field_name: str | None
    form_value: str | None
    label_value: str | None
    result: str | None
    section_v_ref: str | None
    note: str | None
    label_image_id: int | None
    created_at: datetime
    agent_override: str | None
    override_by: int | None
    override_reason: str | None
    override_at: datetime | None


class HardFailureOut(BaseModel):
    """FR-063 -- one DENY-list entry."""

    field_name: str
    form_value: str | None
    label_value: str | None
    description: str


class AllowableRevisionOut(BaseModel):
    """FR-064 -- one RECOMMEND_EXEMPTION_REVIEW-list entry."""

    field_name: str
    discrepancy: str
    section_v_ref: str | None


class DeterminationReportOut(BaseModel):
    """FR-065 -- per-application determination report (WBS 8.3)."""

    application_id: int
    recommendation: str
    comparisons: list[ComparisonOut]
    hard_failures: list[HardFailureOut]
    allowable_revisions: list[AllowableRevisionOut]
    confidence_scores: dict[str, float]
    processed_at: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    permit_no: str | None
    serial_number: str | None
    year: str | None
    form_path: str | None
    product_type: str | None
    source: str | None
    brand_name: str | None
    fanciful_name: str | None
    applicant_name: str | None
    application_type: str | None
    assigned_agent_id: int | None
    status: str
    created_at: datetime
    processed_at: datetime | None

    # Effective determination outcome, if any (FR-090) — surfaced on the
    # applications list so finalized applications show their recommendation.
    recommendation: str | None = None
    finalized_at: datetime | None = None

    # COLA Public Registry forward-compatibility fields (IA-22)
    ttb_id: str | None
    vendor_code: str | None
    class_type_code: str | None
    origin_code: str | None
    registry_status: str | None
    total_bottle_capacity: str | None
    for_sale_in_state: str | None
    qualifications: str | None


class ApplicationDetailOut(ApplicationOut):
    label_images: list[LabelImageOut] = []
    form_parameters: list[FormParameterOut] = []
    label_parameters: list[LabelParameterOut] = []
    determination: DeterminationOut | None = None

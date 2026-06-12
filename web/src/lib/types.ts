// Types mirroring the backend DB schema (DevLog 3.4) and API surface (3.5).
// Endpoints not yet implemented server-side are still typed here so the API
// client and UI can be built against the documented contract ahead of time.

export type ProductType = "wine" | "distilled_spirits" | "malt_beverages";
export type Source = "domestic" | "imported";
export type ApplicationType = "14a" | "14b" | "14c" | "14d";
export type ApplicationStatus =
  | "PENDING"
  | "FORM_ASSESSED"
  | "LABEL_ASSESSED"
  | "COMPARED"
  | "COMPLETE";
export type LabelType = "brand" | "back" | "neck" | "other";
export type ExtractionMethod = "acroform" | "pdftext" | "ai_vision";
export type ComparisonResult =
  | "MATCH"
  | "HARD_FAILURE"
  | "POSSIBLE_ALLOWABLE"
  | "MISSING_FROM_LABEL"
  | "MISSING_FROM_FORM";
export type Recommendation = "APPROVE" | "DENY" | "RECOMMEND_EXEMPTION_REVIEW";

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Agent {
  id: number;
  username: string;
  display_name: string;
  created_at: string;
}

export interface Application {
  id: number;
  serial_number: string | null;
  year: string | null;
  form_path: string | null;
  product_type: ProductType | null;
  source: Source | null;
  brand_name: string | null;
  applicant_name: string | null;
  application_type: ApplicationType | null;
  assigned_agent_id: number | null;
  status: ApplicationStatus;
  created_at: string;
  processed_at: string | null;
  // COLA Public Registry forward-compat fields (Section 6, IA-22)
  ttb_id: string | null;
  vendor_code: string | null;
  class_type_code: string | null;
  origin_code: string | null;
  registry_status: string | null;
  total_bottle_capacity: string | null;
  for_sale_in_state: string | null;
  qualifications: string | null;
}

export interface LabelImage {
  id: number;
  application_id: number;
  image_path: string;
  label_type: LabelType | null;
  uploaded_at: string;
}

export interface FormParameter {
  id: number;
  application_id: number;
  field_name: string;
  field_value: string | null;
  confidence: number | null;
  extraction_method: ExtractionMethod | null;
  location_hint: string | null;
  bbox_json: string | null;
  extracted_at: string;
}

export interface LabelParameter {
  id: number;
  application_id: number;
  label_image_id: number;
  field_name: string;
  field_value: string | null;
  confidence: number | null;
  location_hint: string | null;
  bbox_json: string | null;
  header_height_ratio: number | null;
  extracted_at: string;
}

export interface Comparison {
  id: number;
  application_id: number;
  field_name: string;
  form_value: string | null;
  label_value: string | null;
  result: ComparisonResult;
  section_v_ref: string | null;
  note: string | null;
  label_image_id: number | null;
  created_at: string;
  agent_override: ComparisonResult | null;
  override_by: number | null;
  override_reason: string | null;
  override_at: string | null;
}

export interface Determination {
  id: number;
  application_id: number;
  recommendation: Recommendation;
  hard_failures_json: string | null;
  allowable_json: string | null;
  agent_override: Recommendation | null;
  override_by: number | null;
  override_reason: string | null;
  override_at: string | null;
  finalized_at: string | null;
  created_at: string;
}

export interface Batch {
  id: number;
  name: string | null;
  application_ids: string;
  approved_count: number;
  denied_count: number;
  exemption_count: number;
  summary_json: string | null;
  created_by: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface ApplicationDetail extends Application {
  label_images: LabelImage[];
  form_parameters: FormParameter[];
  label_parameters: LabelParameter[];
  determination: Determination | null;
}

// --- API request/response shapes (3.5) ---

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface BatchProcessRequest {
  application_ids: number[];
}

export interface BatchApplicationStatus {
  id: number;
  status: ApplicationStatus;
  recommendation: Recommendation | null;
}

export interface BatchStatus {
  id: number;
  status: "PROCESSING" | "COMPLETE";
  total: number;
  completed: number;
  approved_count: number;
  denied_count: number;
  exemption_count: number;
  applications: BatchApplicationStatus[];
  created_at: string;
  completed_at: string | null;
}

export interface BatchReport extends BatchStatus {
  most_common_failure: string | null;
}

export interface OverrideDeterminationRequest {
  // omitted/null => overall determination override (FR-089); set => per-parameter (FR-086-088)
  field?: string | null;
  override_value: string;
  reason: string;
}

export interface OverrideResult {
  application_id: number;
  field: string | null;
  original_value: string | null;
  override_value: string;
  override_by: number;
  override_reason: string;
  override_at: string;
}

// --- Settings / API key (runtime-only, never persisted) ---

export interface ApiKeyStatus {
  configured: boolean;
  masked_key: string | null;
  connected: boolean;
  message: string | null;
}

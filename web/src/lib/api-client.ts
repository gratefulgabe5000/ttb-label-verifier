import type {
  ApiKeyStatus,
  Application,
  ApplicationDetail,
  Batch,
  BatchProcessRequest,
  BatchStatus,
  Comparison,
  Determination,
  LoginRequest,
  LoginResponse,
  OverrideDeterminationRequest,
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const AUTH_TOKEN_KEY = "ttb_lvs_token";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message =
      (body && typeof body === "object" && "detail" in body && String(body.detail)) ||
      response.statusText ||
      "Request failed";
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

// Auth is header-based (Bearer token), so files can't be loaded via bare
// <img src> / <Document file="url"> — fetch them as Blobs instead.
async function apiFetchBlob(path: string): Promise<Blob> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { headers });

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText || "Request failed");
  }
  return response.blob();
}

export const healthApi = {
  check: () => apiFetch<{ status: string }>("/health"),
};

// Agent-supplied Anthropic API key — held only in the backend process's
// environment, never persisted to disk or the database.
export const settingsApi = {
  getApiKeyStatus: () => apiFetch<ApiKeyStatus>("/settings/api-key"),
  setApiKey: (apiKey: string) =>
    apiFetch<ApiKeyStatus>("/settings/api-key", {
      method: "PUT",
      body: JSON.stringify({ api_key: apiKey }),
    }),
  deleteApiKey: () => apiFetch<ApiKeyStatus>("/settings/api-key", { method: "DELETE" }),
};

// --- Forward-declared per DevLog 3.5 — backed by WBS 3.0/4.0/5.0/6.0/7.0/8.0,
// not yet implemented server-side. Typed now so UI work can proceed against
// the documented contract.

export const authApi = {
  login: (credentials: LoginRequest) =>
    apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),
};

export interface ApplicationListParams {
  agentId?: number;
  status?: string;
  applicantName?: string;
  page?: number;
  pageSize?: number;
}

function toQueryString(params: object = {}): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const applicationsApi = {
  // GET /applications returns ApplicationOut (no label_images/form_parameters/etc.),
  // which is what `Application` models — use `get()` for the full detail shape.
  list: (params?: ApplicationListParams) => {
    const { applicantName, ...rest } = params ?? {};
    return apiFetch<Application[]>(
      `/applications${toQueryString({ ...rest, applicant_name: applicantName })}`
    );
  },
  upload: (formData: FormData) =>
    apiFetch<ApplicationDetail>("/applications/upload", { method: "POST", body: formData }),
  get: (id: number) => apiFetch<ApplicationDetail>(`/applications/${id}`),
  getFormBlob: (id: number) => apiFetchBlob(`/applications/${id}/form`),
  getLabelImageBlob: (applicationId: number, imageId: number) =>
    apiFetchBlob(`/applications/${applicationId}/label-images/${imageId}`),
  comparisons: (id: number) => apiFetch<Comparison[]>(`/applications/${id}/comparisons`),
  process: (id: number) =>
    apiFetch<ApplicationDetail>(`/applications/${id}/process`, { method: "POST" }),
};

export const batchApi = {
  process: (request: BatchProcessRequest) =>
    apiFetch<BatchStatus>("/batch/process", { method: "POST", body: JSON.stringify(request) }),
  status: (id: number) => apiFetch<BatchStatus>(`/batch/${id}/status`),
  report: (id: number) => apiFetch<Batch>(`/batch/${id}/report`),
};

// TEMPORARY (manual verification of WBS 5.0/6.0) — runs Stage 3 + Stage 4
// extraction and persists the results. Superseded by WBS 9.0 orchestration.
export const debugApi = {
  runExtraction: (applicationId: number) =>
    apiFetch<ApplicationDetail>(`/applications/${applicationId}/debug/extract`, { method: "POST" }),
};

export const determinationsApi = {
  override: (id: number, request: OverrideDeterminationRequest) =>
    apiFetch<Determination>(`/determinations/${id}/override`, {
      method: "POST",
      body: JSON.stringify(request),
    }),
  finalize: (id: number) =>
    apiFetch<Determination>(`/determinations/${id}/finalize`, { method: "POST" }),
};

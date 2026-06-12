import { afterEach, describe, expect, it, vi } from "vitest";
import { useEffect } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ApplicationDetailPage } from "./ApplicationDetailPage";
import { applicationsApi, determinationsApi } from "@/lib/api-client";
import type { ApplicationDetail, Comparison, Determination, LabelParameter } from "@/lib/types";

// react-pdf renders to <canvas> via pdf.js, which jsdom doesn't support —
// stand in with minimal components that still exercise the load callbacks
// FormPdfPanel depends on for sizing the SVG annotation overlay (13.4).
interface MockDocumentProps {
  children: React.ReactNode;
  onLoadSuccess?: (pdf: { numPages: number }) => void;
}
function MockDocument({ children, onLoadSuccess }: MockDocumentProps) {
  useEffect(() => {
    onLoadSuccess?.({ numPages: 1 });
  }, [onLoadSuccess]);
  return <div data-testid="pdf-document">{children}</div>;
}

interface MockPageProps {
  onLoadSuccess?: (page: { width: number; height: number; originalWidth: number; originalHeight: number }) => void;
}
function MockPage({ onLoadSuccess }: MockPageProps) {
  useEffect(() => {
    onLoadSuccess?.({ width: 520, height: 857, originalWidth: 612, originalHeight: 1008 });
  }, [onLoadSuccess]);
  return <div data-testid="pdf-page" />;
}

vi.mock("react-pdf", () => ({
  pdfjs: { GlobalWorkerOptions: {} as Record<string, unknown> },
  Document: MockDocument,
  Page: MockPage,
}));

const APPLICATION: ApplicationDetail = {
  id: 1,
  serial_number: "25304001000123",
  year: null,
  form_path: "/data/uploads/1/form.pdf",
  product_type: "distilled_spirits",
  source: "domestic",
  brand_name: "Stoll & Wolfe",
  applicant_name: "Stoll & Wolfe Distillery",
  application_type: "14a",
  assigned_agent_id: 1,
  status: "PENDING",
  created_at: "2026-06-01T00:00:00Z",
  processed_at: null,
  ttb_id: null,
  vendor_code: null,
  class_type_code: null,
  origin_code: null,
  registry_status: null,
  total_bottle_capacity: null,
  for_sale_in_state: null,
  qualifications: null,
  label_images: [
    {
      id: 10,
      application_id: 1,
      image_path: "/data/uploads/1/label_1.jpg",
      label_type: "brand",
      uploaded_at: "2026-06-01T00:00:00Z",
    },
    {
      id: 11,
      application_id: 1,
      image_path: "/data/uploads/1/label_2.jpg",
      label_type: "back",
      uploaded_at: "2026-06-01T00:00:00Z",
    },
  ],
  form_parameters: [
    {
      id: 100,
      application_id: 1,
      field_name: "brand_name",
      field_value: "Stoll & Wolfe",
      confidence: 1,
      extraction_method: "acroform",
      location_hint: null,
      bbox_json: '{"page":0,"x":21.9,"y":213.4,"w":224.2,"h":15.7}',
      extracted_at: "2026-06-01T00:00:00Z",
    },
  ],
  label_parameters: [],
  determination: null,
};

const LABEL_PARAMETERS: LabelParameter[] = [
  {
    id: 200,
    application_id: 1,
    label_image_id: 10,
    field_name: "applicant_name",
    field_value: "Stoll & Wolfe Distillery",
    confidence: 0.95,
    location_hint: null,
    bbox_json: '{"x":40,"y":60,"w":300,"h":50}',
    header_height_ratio: 0.2,
    extracted_at: "2026-06-01T00:00:00Z",
  },
  {
    id: 201,
    application_id: 1,
    label_image_id: 11,
    field_name: "government_warning",
    field_value: null,
    confidence: null,
    location_hint: null,
    bbox_json: '{"x":10,"y":400,"w":500,"h":80}',
    header_height_ratio: null,
    extracted_at: "2026-06-01T00:00:00Z",
  },
];

const COMPARISONS: Comparison[] = [
  {
    id: 1,
    application_id: 1,
    field_name: "brand_name",
    form_value: "Stoll & Wolfe",
    label_value: "Stoll & Wolfe",
    result: "MATCH",
    section_v_ref: null,
    note: null,
    label_image_id: 10,
    created_at: "2026-06-01T00:10:00Z",
    agent_override: null,
    override_by: null,
    override_reason: null,
    override_at: null,
  },
  {
    id: 2,
    application_id: 1,
    field_name: "government_warning",
    form_value: null,
    label_value: null,
    result: "HARD_FAILURE",
    section_v_ref: "27 CFR 16.21",
    note: "Government warning statement not found on label.",
    label_image_id: 11,
    created_at: "2026-06-01T00:10:00Z",
    agent_override: null,
    override_by: null,
    override_reason: null,
    override_at: null,
  },
];

const DETERMINATION: Determination = {
  id: 500,
  application_id: 1,
  recommendation: "APPROVE",
  hard_failures_json: null,
  allowable_json: null,
  agent_override: null,
  override_by: null,
  override_reason: null,
  override_at: null,
  finalized_at: null,
  created_at: "2026-06-01T00:10:00Z",
};

function renderDetailPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/applications/1"]}>
        <Routes>
          <Route path="/applications/:id" element={<ApplicationDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ApplicationDetailPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the split-view layout with the form PDF and label image tabs (13.1-13.3)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue(APPLICATION);
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue([]);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    renderDetailPage();

    expect(await screen.findByText(/Application #1/)).toBeInTheDocument();
    expect(screen.getByText("Application Form")).toBeInTheDocument();
    expect(screen.getByText("Label Images")).toBeInTheDocument();

    expect(await screen.findByTestId("pdf-document")).toBeInTheDocument();
    expect(await screen.findByRole("tab", { name: /brand/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /back/i })).toBeInTheDocument();
  });

  it("renders the SVG annotation overlay for persisted form parameters (13.4)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue(APPLICATION);
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue([]);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    const { container } = renderDetailPage();

    await screen.findByTestId("pdf-document");

    const rect = await screen.findByText("brand_name: Stoll & Wolfe");
    expect(rect.closest("svg")).not.toBeNull();
    expect(container.querySelector("svg rect")).not.toBeNull();
  });

  it("shows empty states when there are no label images or extracted form fields", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue({ ...APPLICATION, label_images: [], form_parameters: [] });
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue([]);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    renderDetailPage();

    expect(await screen.findByText("No label images uploaded for this application.")).toBeInTheDocument();
    expect(await screen.findByText(/No extracted form fields yet/)).toBeInTheDocument();
  });

  it("renders an SVG annotation overlay for the active label image (13.5)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue({ ...APPLICATION, label_parameters: LABEL_PARAMETERS });
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue([]);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    const { container } = renderDetailPage();

    await screen.findByRole("tab", { name: /brand/i });
    const labelImage = container.querySelector('img[alt="brand"]') as HTMLImageElement;
    Object.defineProperty(labelImage, "naturalWidth", { value: 1000, configurable: true });
    Object.defineProperty(labelImage, "naturalHeight", { value: 800, configurable: true });
    fireEvent.load(labelImage);

    expect(await screen.findByText("applicant_name: Stoll & Wolfe Distillery")).toBeInTheDocument();
    expect(container.querySelector("svg rect")).not.toBeNull();
  });

  it("renders the parameter results table from comparisons (13.7)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue(APPLICATION);
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue(COMPARISONS);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    renderDetailPage();

    expect(await screen.findByText("Brand Name")).toBeInTheDocument();
    expect(screen.getByText("Government Warning statement")).toBeInTheDocument();
    expect(screen.getByText("Match")).toBeInTheDocument();
    expect(screen.getByText("Hard Failure")).toBeInTheDocument();
    expect(screen.getByText("27 CFR 16.21 — Government warning statement not found on label.")).toBeInTheDocument();
  });

  it("cross-highlights matching annotations and auto-switches the label tab on hover (13.6/13.11)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue({ ...APPLICATION, label_parameters: LABEL_PARAMETERS });
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue(COMPARISONS);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    const { container } = renderDetailPage();

    expect(await screen.findByRole("tab", { name: /brand/i })).toHaveAttribute("aria-selected", "true");

    const row = (await screen.findByText("Government Warning statement")).closest("tr");
    expect(row).not.toBeNull();
    await userEvent.hover(row!);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /back/i })).toHaveAttribute("aria-selected", "true");
    });

    const backImage = container.querySelector('img[alt="back"]') as HTMLImageElement;
    Object.defineProperty(backImage, "naturalWidth", { value: 1000, configurable: true });
    Object.defineProperty(backImage, "naturalHeight", { value: 800, configurable: true });
    fireEvent.load(backImage);

    const title = await screen.findByText("government_warning: (empty)");
    expect(title.closest("g")?.querySelector("rect")).toHaveAttribute("stroke", "#2563eb");
  });

  it("supports overall determination override and finalize (13.9/13.10)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue({ ...APPLICATION, determination: DETERMINATION });
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue([]);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));
    vi.spyOn(determinationsApi, "override").mockResolvedValue({
      application_id: 1,
      field: null,
      original_value: "APPROVE",
      override_value: "DENY",
      override_by: 1,
      override_reason: "Found undeclared additive.",
      override_at: "2026-06-12T00:00:00Z",
    });
    vi.spyOn(determinationsApi, "finalize").mockResolvedValue({ ...DETERMINATION, finalized_at: "2026-06-12T00:05:00Z" });

    renderDetailPage();

    expect(await screen.findByText("Approve")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Override" }));
    expect(await screen.findByText("Override Determination")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("New value"), "DENY");
    await userEvent.type(screen.getByLabelText("Reason"), "Found undeclared additive.");
    await userEvent.click(screen.getByRole("button", { name: "Save Override" }));

    await waitFor(() => {
      expect(determinationsApi.override).toHaveBeenCalledWith(500, {
        field: null,
        override_value: "DENY",
        reason: "Found undeclared additive.",
      });
    });
    await waitFor(() => {
      expect(screen.queryByText("Override Determination")).not.toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Finalize" }));

    await waitFor(() => {
      expect(determinationsApi.finalize).toHaveBeenCalledWith(500);
    });
    expect(await screen.findByText("Finalized")).toBeInTheDocument();
  });

  it("opens an override dialog from the results table context menu (13.8)", async () => {
    vi.spyOn(applicationsApi, "get").mockResolvedValue({ ...APPLICATION, determination: DETERMINATION });
    vi.spyOn(applicationsApi, "comparisons").mockResolvedValue(COMPARISONS);
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));
    vi.spyOn(determinationsApi, "override").mockResolvedValue({
      application_id: 1,
      field: "government_warning",
      original_value: "HARD_FAILURE",
      override_value: "MATCH",
      override_by: 1,
      override_reason: "Confirmed present on neck label.",
      override_at: "2026-06-12T00:00:00Z",
    });

    renderDetailPage();

    const row = (await screen.findByText("Government Warning statement")).closest("tr");
    expect(row).not.toBeNull();
    fireEvent.contextMenu(row!);

    await userEvent.click(await screen.findByRole("menuitem", { name: "Override result..." }));
    expect(await screen.findByText("Override: Government Warning statement")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("New value"), "MATCH");
    await userEvent.type(screen.getByLabelText("Reason"), "Confirmed present on neck label.");
    await userEvent.click(screen.getByRole("button", { name: "Save Override" }));

    await waitFor(() => {
      expect(determinationsApi.override).toHaveBeenCalledWith(500, {
        field: "government_warning",
        override_value: "MATCH",
        reason: "Confirmed present on neck label.",
      });
    });
  });
});

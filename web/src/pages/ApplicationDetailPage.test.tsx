import { afterEach, describe, expect, it, vi } from "vitest";
import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ApplicationDetailPage } from "./ApplicationDetailPage";
import { applicationsApi } from "@/lib/api-client";
import type { ApplicationDetail } from "@/lib/types";

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
    vi.spyOn(applicationsApi, "getFormBlob").mockResolvedValue(new Blob(["%PDF"], { type: "application/pdf" }));
    vi.spyOn(applicationsApi, "getLabelImageBlob").mockResolvedValue(new Blob(["img"], { type: "image/jpeg" }));

    renderDetailPage();

    expect(await screen.findByText("No label images uploaded for this application.")).toBeInTheDocument();
    expect(await screen.findByText(/No extracted form fields yet/)).toBeInTheDocument();
  });
});

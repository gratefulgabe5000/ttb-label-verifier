import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { BatchReportPage } from "./BatchReportPage";
import { applicationsApi, batchApi } from "@/lib/api-client";
import type { Application, BatchReport } from "@/lib/types";

const BASE_APPLICATION: Omit<Application, "id" | "applicant_name" | "serial_number"> = {
  permit_no: null,
  year: null,
  form_path: null,
  product_type: "distilled_spirits",
  source: "domestic",
  brand_name: null,
  fanciful_name: null,
  application_type: "14a",
  assigned_agent_id: 1,
  status: "COMPLETE",
  created_at: "2026-06-01T00:00:00Z",
  processed_at: "2026-06-01T00:05:00Z",
  recommendation: null,
  finalized_at: null,
  ttb_id: null,
  vendor_code: null,
  class_type_code: null,
  origin_code: null,
  registry_status: null,
  total_bottle_capacity: null,
  for_sale_in_state: null,
  qualifications: null,
};

const APPLICATIONS: Application[] = [
  { ...BASE_APPLICATION, id: 1, applicant_name: "Stoll & Wolfe Distillery", serial_number: "25304001000123" },
  { ...BASE_APPLICATION, id: 2, applicant_name: "Acme Beverage Co", serial_number: "25304001000456" },
];

const COMPLETE_REPORT: BatchReport = {
  id: 99,
  status: "COMPLETE",
  total: 2,
  completed: 2,
  approved_count: 1,
  denied_count: 1,
  exemption_count: 0,
  applications: [
    { id: 1, status: "COMPLETE", recommendation: "APPROVE" },
    { id: 2, status: "COMPLETE", recommendation: "DENY" },
  ],
  created_at: "2026-06-12T00:00:00Z",
  completed_at: "2026-06-12T00:01:00Z",
  most_common_failure: "Government Warning Statement",
};

function renderBatchReport(batchId = 99) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/batches/${batchId}`]}>
        <Routes>
          <Route path="/batches/:id" element={<BatchReportPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("BatchReportPage", () => {
  beforeEach(() => {
    vi.spyOn(applicationsApi, "list").mockResolvedValue(APPLICATIONS);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders counts by outcome and the most common failure type (14.1/14.2)", async () => {
    vi.spyOn(batchApi, "report").mockResolvedValue(COMPLETE_REPORT);

    renderBatchReport();

    expect(await screen.findByText("Batch #99 Report")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // Total Processed
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Denied")).toBeInTheDocument();
    expect(screen.getByText("Exemption Review")).toBeInTheDocument();
    expect(screen.getByText("Government Warning Statement")).toBeInTheDocument();

    expect(await screen.findByText("Stoll & Wolfe Distillery")).toBeInTheDocument();
    expect(screen.getByText("Acme Beverage Co")).toBeInTheDocument();
    expect(screen.getByText("Approve")).toBeInTheDocument();
    expect(screen.getByText("Deny")).toBeInTheDocument();
  });

  it("shows a processing indicator while the batch is incomplete", async () => {
    vi.spyOn(batchApi, "report").mockResolvedValue({
      ...COMPLETE_REPORT,
      status: "PROCESSING",
      completed: 1,
    });

    renderBatchReport();

    expect(await screen.findByText("Processing: 1 of 2 complete...")).toBeInTheDocument();
    expect(screen.queryByText("Approved")).not.toBeInTheDocument();
  });

  it("shows 'None' when there is no common failure type", async () => {
    vi.spyOn(batchApi, "report").mockResolvedValue({ ...COMPLETE_REPORT, most_common_failure: null });

    renderBatchReport();

    expect(await screen.findByText("None")).toBeInTheDocument();
  });

  it("exports a CSV of application results (14.3)", async () => {
    vi.spyOn(batchApi, "report").mockResolvedValue(COMPLETE_REPORT);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    renderBatchReport();
    await screen.findByText("Stoll & Wolfe Distillery");

    await userEvent.click(screen.getByRole("button", { name: "Export CSV" }));

    expect(clickSpy).toHaveBeenCalledTimes(1);
  });

  it("triggers the browser print dialog for PDF export (14.4)", async () => {
    vi.spyOn(batchApi, "report").mockResolvedValue(COMPLETE_REPORT);
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});

    renderBatchReport();
    await screen.findByText("Stoll & Wolfe Distillery");

    await userEvent.click(screen.getByRole("button", { name: "Print / Save as PDF" }));

    expect(printSpy).toHaveBeenCalledTimes(1);
  });
});

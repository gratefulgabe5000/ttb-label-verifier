import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "./DashboardPage";
import { ApiError, applicationsApi, batchApi } from "@/lib/api-client";
import type { Application, BatchStatus } from "@/lib/types";

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
  status: "PENDING",
  created_at: "2026-06-01T00:00:00Z",
  processed_at: null,
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
  {
    ...BASE_APPLICATION,
    id: 1,
    applicant_name: "Stoll & Wolfe Distillery",
    serial_number: "25304001000123",
    ttb_id: "24308001000001",
    permit_no: "DSP-KY-12345",
    brand_name: "Stoll & Wolfe",
    fanciful_name: "Reserve Select",
    origin_code: "Kentucky",
    class_type_code: "Kentucky Straight Bourbon Whiskey",
  },
  { ...BASE_APPLICATION, id: 2, applicant_name: "Acme Beverage Co", serial_number: "25304001000456" },
];

const BATCH_STATUS: BatchStatus = {
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
};

const PROCESSING_BATCH_STATUS: BatchStatus = {
  id: 99,
  status: "PROCESSING",
  total: 2,
  completed: 0,
  approved_count: 0,
  denied_count: 0,
  exemption_count: 0,
  applications: [],
  created_at: "2026-06-12T00:00:00Z",
  completed_at: null,
};

function renderDashboard() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.spyOn(applicationsApi, "list").mockResolvedValue(APPLICATIONS);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the application list (12.1) and upload action (12.7)", async () => {
    renderDashboard();

    expect(await screen.findByText("25304001000123")).toBeInTheDocument();
    expect(screen.getByText("25304001000456")).toBeInTheDocument();
    expect(screen.getByText("24308001000001")).toBeInTheDocument();
    expect(screen.getByText("DSP-KY-12345")).toBeInTheDocument();
    expect(screen.getByText("Reserve Select")).toBeInTheDocument();
    expect(screen.getByText("Stoll & Wolfe")).toBeInTheDocument();
    expect(screen.getByText("Kentucky")).toBeInTheDocument();
    expect(screen.getByText("Kentucky Straight Bourbon Whiskey")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New Upload" })).toBeInTheDocument();
  });

  it("filters across all columns by any matching value (12.2)", async () => {
    renderDashboard();
    await screen.findByText("25304001000123");
    expect(screen.getByText("25304001000456")).toBeInTheDocument();

    const input = screen.getByPlaceholderText("Filter applications...");
    await userEvent.type(input, "Stoll");

    // Matches application 1 (applicant name "Stoll & Wolfe Distillery") and hides application 2.
    expect(screen.getByText("25304001000123")).toBeInTheDocument();
    expect(screen.queryByText("25304001000456")).not.toBeInTheDocument();
  });

  it("shows a 'no applications found' message when the filter matches nothing (12.2)", async () => {
    renderDashboard();
    await screen.findByText("25304001000123");

    const input = screen.getByPlaceholderText("Filter applications...");
    await userEvent.type(input, "nonexistent");

    expect(await screen.findByText(/No applications found for "nonexistent"/)).toBeInTheDocument();
  });

  it("sorts rows when a column header is clicked, toggling direction on repeat clicks", async () => {
    renderDashboard();
    await screen.findByText("25304001000123");

    const bodyRowTexts = () =>
      screen
        .getAllByRole("row")
        .slice(1)
        .map((row) => row.textContent ?? "");

    // Default order matches the API response: application 1 (brand "Stoll & Wolfe") first.
    expect(bodyRowTexts()[0]).toContain("Stoll & Wolfe");

    await userEvent.click(screen.getByRole("button", { name: /Brand Name/ }));

    // Ascending: application 2 (no brand name, sorts as "") comes before "Stoll & Wolfe".
    expect(bodyRowTexts()[0]).not.toContain("Stoll & Wolfe");

    await userEvent.click(screen.getByRole("button", { name: /Brand Name/ }));

    // Second click toggles to descending, restoring "Stoll & Wolfe" to the first row.
    expect(bodyRowTexts()[0]).toContain("Stoll & Wolfe");
  });

  it("supports batch checkbox selection (12.3)", async () => {
    renderDashboard();
    await screen.findByText("25304001000123");

    const checkboxes = screen.getAllByRole("checkbox");
    await userEvent.click(checkboxes[1]);
    expect(await screen.findByText("1 selected")).toBeInTheDocument();

    await userEvent.click(checkboxes[2]);
    expect(await screen.findByText("2 selected")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.queryByText(/selected/)).not.toBeInTheDocument();
  });

  it("processes selected applications and shows the batch summary header (12.4/12.6)", async () => {
    vi.spyOn(batchApi, "process").mockResolvedValue(BATCH_STATUS);
    vi.spyOn(batchApi, "status").mockResolvedValue(BATCH_STATUS);

    renderDashboard();
    await screen.findByText("25304001000123");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    await waitFor(() => {
      expect(batchApi.process).toHaveBeenCalledWith({ application_ids: [1] });
    });

    expect(await screen.findByText("Batch #99: 2 of 2 processed")).toBeInTheDocument();
    expect(screen.getByText("1 approved")).toBeInTheDocument();
    expect(screen.getByText("1 denied")).toBeInTheDocument();
    expect(screen.getByText("0 exemption review")).toBeInTheDocument();
  });

  it("links to the batch report once processing completes (14.0 wiring)", async () => {
    vi.spyOn(batchApi, "process").mockResolvedValue(BATCH_STATUS);
    vi.spyOn(batchApi, "status").mockResolvedValue(BATCH_STATUS);

    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/batches/:id" element={<p>Batch Report {99}</p>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
    await screen.findByText("25304001000123");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    await userEvent.click(await screen.findByRole("button", { name: "View Report" }));
    expect(await screen.findByText("Batch Report 99")).toBeInTheDocument();
  });

  it("shows a plain-English error with retry/dismiss when batch status polling fails (15.5)", async () => {
    vi.spyOn(batchApi, "process").mockResolvedValue(PROCESSING_BATCH_STATUS);
    vi.spyOn(batchApi, "status").mockRejectedValue(new ApiError(500, "Internal server error"));

    renderDashboard();
    await screen.findByText("25304001000123");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    expect(await screen.findByText(/Failed to load status for batch #99/)).toBeInTheDocument();
    const retryButton = screen.getByRole("button", { name: "Retry" });
    const dismissButton = screen.getByRole("button", { name: "Dismiss" });
    expect(retryButton).toBeInTheDocument();

    await userEvent.click(dismissButton);
    expect(screen.queryByText(/Failed to load status for batch/)).not.toBeInTheDocument();
  });

  it("shows recommendation result badges for applications in the batch result (12.5)", async () => {
    vi.spyOn(batchApi, "process").mockResolvedValue(BATCH_STATUS);
    vi.spyOn(batchApi, "status").mockResolvedValue(BATCH_STATUS);

    renderDashboard();
    await screen.findByText("25304001000123");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    expect(await screen.findByText("Approve")).toBeInTheDocument();
    expect(screen.getByText("Deny")).toBeInTheDocument();
  });
});

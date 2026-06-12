import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "./DashboardPage";
import { applicationsApi, batchApi } from "@/lib/api-client";
import type { Application, BatchStatus } from "@/lib/types";

const BASE_APPLICATION: Omit<Application, "id" | "applicant_name" | "serial_number"> = {
  year: null,
  form_path: null,
  product_type: "distilled_spirits",
  source: "domestic",
  brand_name: null,
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
};

const APPLICATIONS: Application[] = [
  { ...BASE_APPLICATION, id: 1, applicant_name: "Stoll & Wolfe Distillery", serial_number: "25304001000123" },
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

    expect(await screen.findByText("Stoll & Wolfe Distillery")).toBeInTheDocument();
    expect(screen.getByText("Acme Beverage Co")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New Upload" })).toBeInTheDocument();
  });

  it("filters by applicant name (12.2)", async () => {
    renderDashboard();
    await screen.findByText("Stoll & Wolfe Distillery");

    const input = screen.getByPlaceholderText("Filter by applicant...");
    await userEvent.type(input, "Stoll");

    await waitFor(() => {
      expect(applicationsApi.list).toHaveBeenLastCalledWith({ applicantName: "Stoll" });
    });
  });

  it("supports batch checkbox selection (12.3)", async () => {
    renderDashboard();
    await screen.findByText("Stoll & Wolfe Distillery");

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
    await screen.findByText("Stoll & Wolfe Distillery");

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
    await screen.findByText("Stoll & Wolfe Distillery");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    await userEvent.click(await screen.findByRole("button", { name: "View Report" }));
    expect(await screen.findByText("Batch Report 99")).toBeInTheDocument();
  });

  it("shows recommendation result badges for applications in the batch result (12.5)", async () => {
    vi.spyOn(batchApi, "process").mockResolvedValue(BATCH_STATUS);
    vi.spyOn(batchApi, "status").mockResolvedValue(BATCH_STATUS);

    renderDashboard();
    await screen.findByText("Stoll & Wolfe Distillery");

    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Process Selected" }));

    expect(await screen.findByText("Approve")).toBeInTheDocument();
    expect(screen.getByText("Deny")).toBeInTheDocument();
  });
});

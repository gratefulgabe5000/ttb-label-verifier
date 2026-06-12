import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "./DashboardPage";
import { applicationsApi } from "@/lib/api-client";
import type { Application } from "@/lib/types";

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
});

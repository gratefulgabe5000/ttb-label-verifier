import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApiKeyStatusBadge } from "./ApiKeyStatusBadge";
import { settingsApi } from "@/lib/api-client";

function renderBadge(onOpenSettings: () => void) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <ApiKeyStatusBadge onOpenSettings={onOpenSettings} />
    </QueryClientProvider>
  );
}

describe("ApiKeyStatusBadge", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows a green badge and opens settings on click when the key is configured and connected", async () => {
    vi.spyOn(settingsApi, "getApiKeyStatus").mockResolvedValue({
      configured: true,
      connected: true,
      masked_key: "sk-...abcd",
      message: null,
    });
    const onOpenSettings = vi.fn();

    renderBadge(onOpenSettings);

    const badge = await screen.findByText("AI Key");
    expect(badge.closest("span")).toHaveClass("bg-green-100");

    await userEvent.click(screen.getByRole("button"));
    expect(onOpenSettings).toHaveBeenCalled();
  });

  it("shows an amber badge when the key is not configured", async () => {
    vi.spyOn(settingsApi, "getApiKeyStatus").mockResolvedValue({
      configured: false,
      connected: false,
      masked_key: null,
      message: null,
    });
    const onOpenSettings = vi.fn();

    renderBadge(onOpenSettings);

    const badge = await screen.findByText("AI Key");
    expect(badge.closest("span")).toHaveClass("bg-amber-100");

    await userEvent.click(screen.getByRole("button"));
    expect(onOpenSettings).toHaveBeenCalled();
  });
});

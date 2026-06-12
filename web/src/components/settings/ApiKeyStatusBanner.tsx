import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { API_KEY_QUERY_KEY, settingsApi } from "@/lib/api-client";

interface ApiKeyStatusBannerProps {
  onOpenSettings: () => void;
}

/** Always-visible indicator of whether an Anthropic API key is configured and
 * connected, directly below the app header (gear icon / profile menu). */
export function ApiKeyStatusBanner({ onOpenSettings }: ApiKeyStatusBannerProps) {
  const statusQuery = useQuery({
    queryKey: API_KEY_QUERY_KEY,
    queryFn: settingsApi.getApiKeyStatus,
  });

  const status = statusQuery.data;

  if (statusQuery.isLoading) {
    return (
      <div className="flex items-center justify-end gap-2 border-b px-4 py-1.5 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 animate-spin" />
        <span>Checking AI API key status...</span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  if (status.configured && status.connected) {
    return (
      <div className="flex items-center justify-end gap-2 border-b bg-green-50 px-4 py-1.5 text-xs text-green-800 dark:bg-green-950 dark:text-green-200">
        <CheckCircle2 className="size-3.5" />
        <span>AI API key configured ({status.masked_key}) — label assessment enabled.</span>
      </div>
    );
  }

  const message = !status.configured
    ? "AI API key needed — label assessment (Stage 4) will return empty results until one is configured."
    : (status.message ?? "AI API key is configured but not connected.");

  return (
    <div className="flex items-center justify-end gap-2 border-b bg-amber-50 px-4 py-1.5 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-200">
      <AlertTriangle className="size-3.5" />
      <span>{message}</span>
      <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={onOpenSettings}>
        Open Settings
      </Button>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { API_KEY_QUERY_KEY, settingsApi } from "@/lib/api-client";

interface ApiKeyStatusBadgeProps {
  onOpenSettings: () => void;
}

/** Compact, always-visible indicator of whether an Anthropic API key is
 * configured and connected. Sits in the app header to the left of the
 * Settings gear icon; click opens Settings. */
export function ApiKeyStatusBadge({ onOpenSettings }: ApiKeyStatusBadgeProps) {
  const statusQuery = useQuery({
    queryKey: API_KEY_QUERY_KEY,
    queryFn: settingsApi.getApiKeyStatus,
  });

  const status = statusQuery.data;

  if (statusQuery.isLoading) {
    return (
      <Badge variant="outline" title="Checking AI API key status...">
        <Loader2 className="size-3 animate-spin" />
      </Badge>
    );
  }

  if (!status) {
    return null;
  }

  if (status.configured && status.connected) {
    return (
      <button type="button" onClick={onOpenSettings}>
        <Badge
          className="gap-1 bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200"
          title={`AI API key configured (${status.masked_key}) — label assessment enabled.`}
        >
          <CheckCircle2 className="size-3" />
          AI Key
        </Badge>
      </button>
    );
  }

  const message = !status.configured
    ? "AI API key needed — label assessment (Stage 4) will return empty results until one is configured."
    : (status.message ?? "AI API key is configured but not connected.");

  return (
    <button type="button" onClick={onOpenSettings}>
      <Badge
        className="gap-1 bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
        title={message}
      >
        <AlertTriangle className="size-3" />
        AI Key
      </Badge>
    </button>
  );
}

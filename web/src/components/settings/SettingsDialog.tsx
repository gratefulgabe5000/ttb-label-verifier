import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_KEY_QUERY_KEY, ApiError, settingsApi } from "@/lib/api-client";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [apiKeyInput, setApiKeyInput] = useState("");
  const queryClient = useQueryClient();

  const statusQuery = useQuery({
    queryKey: API_KEY_QUERY_KEY,
    queryFn: settingsApi.getApiKeyStatus,
    enabled: open,
  });

  const saveMutation = useMutation({
    mutationFn: settingsApi.setApiKey,
    onSuccess: (status) => {
      queryClient.setQueryData(API_KEY_QUERY_KEY, status);
      setApiKeyInput("");
    },
  });

  const removeMutation = useMutation({
    mutationFn: settingsApi.deleteApiKey,
    onSuccess: (status) => {
      queryClient.setQueryData(API_KEY_QUERY_KEY, status);
    },
  });

  const status = statusQuery.data;
  const isBusy = saveMutation.isPending || removeMutation.isPending;

  const handleSave = () => {
    const trimmed = apiKeyInput.trim();
    if (!trimmed) return;
    saveMutation.mutate(trimmed);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Provide your Anthropic API key to enable AI-assisted form and label
            review. The key is held only in the backend server's memory for
            this session — it is never written to disk or stored in the
            database.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic-api-key">Anthropic API key</Label>
            <div className="flex items-center gap-2">
              <Input
                id="anthropic-api-key"
                type="password"
                placeholder={status?.configured ? (status.masked_key ?? "") : "sk-ant-..."}
                value={apiKeyInput}
                onChange={(event) => setApiKeyInput(event.target.value)}
                autoComplete="off"
              />
              <Button onClick={handleSave} disabled={!apiKeyInput.trim() || isBusy}>
                {saveMutation.isPending ? <Loader2 className="size-4 animate-spin" /> : "Save"}
              </Button>
            </div>
          </div>

          <div className="rounded-md border p-3 text-sm">
            {statusQuery.isLoading ? (
              <p className="text-muted-foreground">Checking key status...</p>
            ) : status?.configured ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="size-4 text-green-600" />
                  <span>Key configured: {status.masked_key}</span>
                </div>
                <div className="flex items-center gap-2">
                  {status.connected ? (
                    <CheckCircle2 className="size-4 text-green-600" />
                  ) : (
                    <XCircle className="size-4 text-destructive" />
                  )}
                  <span className={status.connected ? "text-green-600" : "text-destructive"}>
                    {status.message ?? (status.connected ? "Connected" : "Not connected")}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => removeMutation.mutate()}
                  disabled={isBusy}
                >
                  {removeMutation.isPending ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    "Remove key"
                  )}
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-muted-foreground">
                <XCircle className="size-4" />
                <span>No API key configured for this session.</span>
              </div>
            )}
          </div>

          {saveMutation.isError && (
            <p className="text-sm text-destructive">
              {saveMutation.error instanceof ApiError
                ? saveMutation.error.message
                : "Failed to save the API key. Please try again."}
            </p>
          )}

          <div className="space-y-2 border-t pt-4">
            <h3 className="text-sm font-semibold">About...</h3>
            <p className="text-sm text-muted-foreground">
              Open product questions that need a decision from the end user /
              product team. These affect how Stage 5 comparisons are scored,
              so resolve them before relying on automated determinations for
              the cases below.
            </p>
            <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">
                  Importer vs. manufacturer for Item 8 (Applicant Name/Address) on
                  imported products:
                </span>{" "}
                For applications marked "Imported", Item 8 is filled in by the
                U.S. importer, but the label's bottler/producer fields usually
                identify the foreign manufacturer. The comparison engine now
                checks Item 8 against both the label's bottler and importer
                fields (<code>compare_applicant_name</code> /{" "}
                <code>compare_applicant_address</code> in{" "}
                <code>comparison_engine.py</code>), but it's not yet confirmed
                whether Item 8 should always be expected to match the
                importer, the manufacturer, or either for imported-item
                applications.
              </li>
            </ul>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

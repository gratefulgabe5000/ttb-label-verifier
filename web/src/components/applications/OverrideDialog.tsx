import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ApiError, determinationsApi } from "@/lib/api-client";

export interface OverrideOption {
  value: string;
  label: string;
}

interface OverrideDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  applicationId: number;
  determinationId: number;
  field: string | null;
  title: string;
  currentValue: string;
  options: OverrideOption[];
}

export function OverrideDialog({
  open,
  onOpenChange,
  applicationId,
  determinationId,
  field,
  title,
  currentValue,
  options,
}: OverrideDialogProps) {
  const queryClient = useQueryClient();
  const [overrideValue, setOverrideValue] = useState(currentValue);
  const [reason, setReason] = useState("");
  const [prevOpen, setPrevOpen] = useState(open);

  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setOverrideValue(currentValue);
      setReason("");
    }
  }

  const mutation = useMutation({
    mutationFn: () =>
      determinationsApi.override(determinationId, { field, override_value: overrideValue, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application", applicationId] });
      queryClient.invalidateQueries({ queryKey: ["comparisons", applicationId] });
      toast.success("Override saved.");
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to save override.");
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            Record an agent override and the reason for the change. The original AI-determined value is
            preserved for audit (FR-088).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="override-value">New value</Label>
            <select
              id="override-value"
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={overrideValue}
              onChange={(event) => setOverrideValue(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="override-reason">Reason</Label>
            <textarea
              id="override-reason"
              className="min-h-20 w-full rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Explain why this override is being made..."
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={() => mutation.mutate()} disabled={!reason.trim() || mutation.isPending}>
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Save Override
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

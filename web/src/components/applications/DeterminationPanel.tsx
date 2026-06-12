import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RecommendationBadge } from "@/components/applications/RecommendationBadge";
import { OverrideDialog, type OverrideOption } from "@/components/applications/OverrideDialog";
import { ApiError, determinationsApi } from "@/lib/api-client";
import type { ApplicationDetail, Recommendation } from "@/lib/types";

const RECOMMENDATION_OPTIONS: OverrideOption[] = [
  { value: "APPROVE", label: "Approve" },
  { value: "DENY", label: "Deny" },
  { value: "RECOMMEND_EXEMPTION_REVIEW", label: "Recommend Exemption Review" },
];

interface DeterminationPanelProps {
  application: ApplicationDetail;
}

export function DeterminationPanel({ application }: DeterminationPanelProps) {
  const determination = application.determination;
  const queryClient = useQueryClient();
  const [overrideOpen, setOverrideOpen] = useState(false);

  const finalizeMutation = useMutation({
    mutationFn: () => determinationsApi.finalize(determination!.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", application.id], {
        ...application,
        status: "FINALIZED",
        recommendation: updated.agent_override ?? updated.recommendation,
        finalized_at: updated.finalized_at,
        determination: updated,
      });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Determination finalized.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to finalize determination.");
    },
  });

  if (!determination) {
    return null;
  }

  const effective: Recommendation = determination.agent_override ?? determination.recommendation;
  const isFinalized = determination.finalized_at !== null;

  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">Recommended action:</span>
        <RecommendationBadge recommendation={effective} />
        {determination.agent_override && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            overridden from <RecommendationBadge recommendation={determination.recommendation} />
          </span>
        )}
      </div>
      <div className="ml-auto flex items-center gap-2">
        {isFinalized ? (
          <Badge variant="secondary">Finalized</Badge>
        ) : (
          <>
            <Button variant="outline" size="sm" onClick={() => setOverrideOpen(true)}>
              Override
            </Button>
            <Button size="sm" onClick={() => finalizeMutation.mutate()} disabled={finalizeMutation.isPending}>
              {finalizeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Finalize
            </Button>
          </>
        )}
      </div>
      <OverrideDialog
        open={overrideOpen}
        onOpenChange={setOverrideOpen}
        applicationId={application.id}
        determinationId={determination.id}
        field={null}
        title="Override Determination"
        currentValue={effective}
        options={RECOMMENDATION_OPTIONS}
      />
    </div>
  );
}

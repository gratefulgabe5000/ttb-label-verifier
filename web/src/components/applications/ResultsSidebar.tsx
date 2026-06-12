import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, RotateCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { ComparisonResultBadge } from "@/components/applications/ComparisonResultBadge";
import { DeterminationPanel } from "@/components/applications/DeterminationPanel";
import { OverrideDialog, type OverrideOption } from "@/components/applications/OverrideDialog";
import { ApiError, applicationsApi } from "@/lib/api-client";
import { fieldLabel } from "@/lib/field-labels";
import { isFieldHighlighted } from "@/lib/field-mappings";
import { cn } from "@/lib/utils";
import type { ApplicationDetail, Comparison, ComparisonResult } from "@/lib/types";

const COMPARISON_RESULT_OPTIONS: OverrideOption[] = [
  { value: "MATCH", label: "Match" },
  { value: "HARD_FAILURE", label: "Hard Failure" },
  { value: "POSSIBLE_ALLOWABLE", label: "Possible Allowable Revision" },
  { value: "MISSING_FROM_LABEL", label: "Missing from Label" },
  { value: "MISSING_FROM_FORM", label: "Missing from Form" },
];

interface ResultsSidebarProps {
  application: ApplicationDetail;
  comparisons: Comparison[];
  isLoading: boolean;
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
  pinnedField: string | null;
  onSelectField: (field: string) => void;
}

export function ResultsSidebar({
  application,
  comparisons,
  isLoading,
  hoveredField,
  onHoverField,
  pinnedField,
  onSelectField,
}: ResultsSidebarProps) {
  const [overrideTarget, setOverrideTarget] = useState<Comparison | null>(null);
  const queryClient = useQueryClient();

  const determinationId = application.determination?.id ?? null;
  const finalized = application.determination?.finalized_at != null;
  const canOverride = determinationId !== null && !finalized;

  const reprocessMutation = useMutation({
    mutationFn: () => applicationsApi.process(application.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", application.id], updated);
      queryClient.invalidateQueries({ queryKey: ["comparisons", application.id] });
      toast.success("Application reprocessed.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to reprocess application.");
    },
  });

  const reprocessComparisonMutation = useMutation({
    mutationFn: () => applicationsApi.reprocessComparison(application.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", application.id], updated);
      queryClient.invalidateQueries({ queryKey: ["comparisons", application.id] });
      toast.success("Comparison reprocessed.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to reprocess comparison.");
    },
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application #{application.id}</CardTitle>
          <CardAction>
            <Button
              variant="outline"
              size="sm"
              onClick={() => reprocessMutation.mutate()}
              disabled={reprocessMutation.isPending}
            >
              {reprocessMutation.isPending && <Loader2 className="size-4 animate-spin" />}
              Reprocess
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          <DeterminationPanel application={application} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Results</CardTitle>
          <CardAction>
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full"
              aria-label="Reprocess comparison"
              onClick={() => reprocessComparisonMutation.mutate()}
              disabled={reprocessComparisonMutation.isPending}
            >
              <RotateCw
                className={cn("size-4", reprocessComparisonMutation.isPending && "animate-spin")}
              />
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading comparison results...</p>
          ) : comparisons.length === 0 ? (
            <p className="text-sm text-muted-foreground">No comparison results yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {comparisons.map((comparison) => {
                  const effective: ComparisonResult = comparison.agent_override ?? comparison.result;
                  const rowClassName = cn(
                    "cursor-pointer",
                    isFieldHighlighted(hoveredField, comparison.field_name, "comparison") && "bg-accent/50",
                    isFieldHighlighted(pinnedField, comparison.field_name, "comparison") && "border-l-2 border-l-primary"
                  );
                  const rowHandlers = {
                    onMouseEnter: () => onHoverField(comparison.field_name),
                    onMouseLeave: () => onHoverField(null),
                    onClick: () => onSelectField(comparison.field_name),
                  };
                  const cells = (
                    <>
                      <TableCell className="whitespace-normal font-medium">
                        {fieldLabel(comparison.field_name)}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col items-start gap-1">
                          <ComparisonResultBadge result={effective} />
                          {comparison.agent_override && (
                            <span className="text-xs text-muted-foreground">
                              overridden from <ComparisonResultBadge result={comparison.result} />
                            </span>
                          )}
                        </div>
                      </TableCell>
                    </>
                  );

                  if (!canOverride) {
                    return (
                      <TableRow key={comparison.id} className={rowClassName} {...rowHandlers}>
                        {cells}
                      </TableRow>
                    );
                  }

                  return (
                    <ContextMenu key={comparison.id}>
                      <ContextMenuTrigger
                        render={
                          <TableRow className={rowClassName} {...rowHandlers}>
                            {cells}
                          </TableRow>
                        }
                      />
                      <ContextMenuContent>
                        <ContextMenuItem onClick={() => setOverrideTarget(comparison)}>
                          Override result...
                        </ContextMenuItem>
                      </ContextMenuContent>
                    </ContextMenu>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {determinationId !== null && (
        <OverrideDialog
          open={overrideTarget !== null}
          onOpenChange={(open) => {
            if (!open) setOverrideTarget(null);
          }}
          applicationId={application.id}
          determinationId={determinationId}
          field={overrideTarget?.field_name ?? null}
          title={overrideTarget ? `Override: ${fieldLabel(overrideTarget.field_name)}` : "Override"}
          currentValue={overrideTarget ? overrideTarget.agent_override ?? overrideTarget.result : "MATCH"}
          options={COMPARISON_RESULT_OPTIONS}
        />
      )}
    </div>
  );
}

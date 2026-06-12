import { useState } from "react";
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
import { OverrideDialog, type OverrideOption } from "@/components/applications/OverrideDialog";
import { fieldLabel } from "@/lib/field-labels";
import { cn } from "@/lib/utils";
import type { Comparison, ComparisonResult } from "@/lib/types";

const COMPARISON_RESULT_OPTIONS: OverrideOption[] = [
  { value: "MATCH", label: "Match" },
  { value: "HARD_FAILURE", label: "Hard Failure" },
  { value: "POSSIBLE_ALLOWABLE", label: "Possible Allowable Revision" },
  { value: "MISSING_FROM_LABEL", label: "Missing from Label" },
  { value: "MISSING_FROM_FORM", label: "Missing from Form" },
];

interface ParameterResultsTableProps {
  comparisons: Comparison[];
  isLoading: boolean;
  applicationId: number;
  determinationId: number | null;
  finalized: boolean;
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
}

export function ParameterResultsTable({
  comparisons,
  isLoading,
  applicationId,
  determinationId,
  finalized,
  hoveredField,
  onHoverField,
}: ParameterResultsTableProps) {
  const [overrideTarget, setOverrideTarget] = useState<Comparison | null>(null);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading comparison results...</p>;
  }
  if (comparisons.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No comparison results yet — use &quot;Process Selected&quot; on the dashboard to run the comparison.
      </p>
    );
  }

  const canOverride = determinationId !== null && !finalized;

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Field</TableHead>
            <TableHead>Form Value</TableHead>
            <TableHead>Label Value</TableHead>
            <TableHead>Result</TableHead>
            <TableHead>Reference / Note</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {comparisons.map((comparison) => {
            const effective: ComparisonResult = comparison.agent_override ?? comparison.result;
            const cells = (
              <>
                <TableCell className="font-medium">{fieldLabel(comparison.field_name)}</TableCell>
                <TableCell className="whitespace-normal">{comparison.form_value ?? "—"}</TableCell>
                <TableCell className="whitespace-normal">{comparison.label_value ?? "—"}</TableCell>
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
                <TableCell className="whitespace-normal text-muted-foreground">
                  {[comparison.section_v_ref, comparison.note].filter(Boolean).join(" — ") || "—"}
                </TableCell>
              </>
            );

            const rowClassName = cn(
              "cursor-default",
              hoveredField === comparison.field_name && "bg-accent/50"
            );
            const rowHandlers = {
              onMouseEnter: () => onHoverField(comparison.field_name),
              onMouseLeave: () => onHoverField(null),
            };

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

      {determinationId !== null && (
        <OverrideDialog
          open={overrideTarget !== null}
          onOpenChange={(open) => {
            if (!open) setOverrideTarget(null);
          }}
          applicationId={applicationId}
          determinationId={determinationId}
          field={overrideTarget?.field_name ?? null}
          title={overrideTarget ? `Override: ${fieldLabel(overrideTarget.field_name)}` : "Override"}
          currentValue={overrideTarget ? overrideTarget.agent_override ?? overrideTarget.result : "MATCH"}
          options={COMPARISON_RESULT_OPTIONS}
        />
      )}
    </>
  );
}

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { isFieldHighlighted } from "@/lib/field-mappings";
import { cn } from "@/lib/utils";
import type { Comparison } from "@/lib/types";

interface ParameterResultsTableProps {
  comparisons: Comparison[];
  isLoading: boolean;
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
  pinnedField: string | null;
  onSelectField: (field: string) => void;
}

export function ParameterResultsTable({
  comparisons,
  isLoading,
  hoveredField,
  onHoverField,
  pinnedField,
  onSelectField,
}: ParameterResultsTableProps) {
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

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Form Value</TableHead>
          <TableHead>Label Value</TableHead>
          <TableHead>Reference / Note</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {comparisons.map((comparison) => {
          const rowClassName = cn(
            "cursor-pointer",
            isFieldHighlighted(hoveredField, comparison.field_name, "comparison") && "bg-accent/50",
            isFieldHighlighted(pinnedField, comparison.field_name, "comparison") && "border-l-2 border-l-primary"
          );

          return (
            <TableRow
              key={comparison.id}
              className={rowClassName}
              onMouseEnter={() => onHoverField(comparison.field_name)}
              onMouseLeave={() => onHoverField(null)}
              onClick={() => onSelectField(comparison.field_name)}
            >
              <TableCell className="whitespace-normal">{comparison.form_value ?? "—"}</TableCell>
              <TableCell className="whitespace-normal">{comparison.label_value ?? "—"}</TableCell>
              <TableCell className="whitespace-normal text-muted-foreground">
                {[comparison.section_v_ref, comparison.note].filter(Boolean).join(" — ") || "—"}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

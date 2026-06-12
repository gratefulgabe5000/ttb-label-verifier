import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ComparisonResult } from "@/lib/types";

const RESULT_CONFIG: Record<ComparisonResult, { label: string; icon: string; className: string }> = {
  MATCH: { label: "Match", icon: "✅", className: "border-emerald-600 text-emerald-700 dark:text-emerald-400" },
  HARD_FAILURE: { label: "Hard Failure", icon: "❌", className: "border-destructive text-destructive" },
  POSSIBLE_ALLOWABLE: {
    label: "Possible Allowable Revision",
    icon: "⚠️",
    className: "border-amber-600 text-amber-700 dark:text-amber-400",
  },
  MISSING_FROM_LABEL: {
    label: "Missing from Label",
    icon: "⚠️",
    className: "border-amber-600 text-amber-700 dark:text-amber-400",
  },
  MISSING_FROM_FORM: {
    label: "Missing from Form",
    icon: "⚠️",
    className: "border-amber-600 text-amber-700 dark:text-amber-400",
  },
};

interface ComparisonResultBadgeProps {
  result: ComparisonResult;
}

export function ComparisonResultBadge({ result }: ComparisonResultBadgeProps) {
  const config = RESULT_CONFIG[result];
  return (
    <Badge variant="outline" className={cn("whitespace-nowrap", config.className)}>
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </Badge>
  );
}

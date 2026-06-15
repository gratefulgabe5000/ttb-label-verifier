import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/lib/types";

const RECOMMENDATION_CONFIG: Record<Recommendation, { label: string; icon: string; className: string }> = {
  APPROVE: { label: "Approve", icon: "✅", className: "border-emerald-600 text-emerald-700 dark:text-emerald-400" },
  DENY: { label: "Deny", icon: "❌", className: "border-destructive text-destructive" },
  RECOMMEND_EXEMPTION_REVIEW: {
    label: "Exemption Review",
    icon: "⚠️",
    className: "border-amber-600 text-amber-700 dark:text-amber-400",
  },
};

// Past-tense labels for a *finalized* application (the action has already been
// taken), vs. the present-tense "Recommended action" shown before finalization.
const PAST_TENSE_LABELS: Record<Recommendation, string> = {
  APPROVE: "Approved",
  DENY: "Denied",
  RECOMMEND_EXEMPTION_REVIEW: "Recommended for Exemption Review",
};

interface RecommendationBadgeProps {
  recommendation: Recommendation | null | undefined;
  tense?: "present" | "past";
}

export function RecommendationBadge({ recommendation, tense = "present" }: RecommendationBadgeProps) {
  if (!recommendation) {
    return <span className="text-sm text-muted-foreground">&mdash;</span>;
  }

  const config = RECOMMENDATION_CONFIG[recommendation];
  const label = tense === "past" ? PAST_TENSE_LABELS[recommendation] : config.label;
  return (
    <Badge variant="outline" className={cn(config.className)}>
      <span aria-hidden="true">{config.icon}</span>
      {label}
    </Badge>
  );
}

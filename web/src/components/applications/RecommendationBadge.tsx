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

interface RecommendationBadgeProps {
  recommendation: Recommendation | null | undefined;
}

export function RecommendationBadge({ recommendation }: RecommendationBadgeProps) {
  if (!recommendation) {
    return <span className="text-sm text-muted-foreground">&mdash;</span>;
  }

  const config = RECOMMENDATION_CONFIG[recommendation];
  return (
    <Badge variant="outline" className={cn(config.className)}>
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </Badge>
  );
}

import { Badge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icon";
import type {
  AiCandidateCompareConfidence,
  HiringRecommendation
} from "@/lib/api/types/ai-candidate-compare";
import { cn } from "@/lib/cn";

const CONFIDENCE_LABEL: Record<AiCandidateCompareConfidence, string> = {
  high: "High",
  medium: "Medium",
  low: "Low"
};

function confidenceTone(
  confidence: AiCandidateCompareConfidence
): "success" | "warning" | "neutral" {
  if (confidence === "high") return "success";
  if (confidence === "medium") return "warning";
  return "neutral";
}

export type HiringRecommendationCardProps = Readonly<{
  leaderName: string;
  confidence: AiCandidateCompareConfidence;
  recommendation: HiringRecommendation;
  className?: string;
}>;

export function HiringRecommendationCard({
  leaderName,
  confidence,
  recommendation,
  className
}: HiringRecommendationCardProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-card border border-accent/35 bg-surface shadow-card",
        className
      )}
      aria-labelledby="hiring-recommendation-heading"
      role="region"
    >
      <div className="border-b border-accent/20 bg-accent-soft/70 px-5 py-4 sm:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <span
            className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-accent text-accent-foreground shadow-sm shadow-accent/30"
            aria-hidden="true"
          >
            <Icon name="check-circle" className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-muted">
              Advisory
            </p>
            <h3
              id="hiring-recommendation-heading"
              className="text-base font-semibold tracking-tight text-ink sm:text-lg"
            >
              Hiring Recommendation
            </h3>
          </div>
        </div>
      </div>

      <div className="grid gap-0 sm:grid-cols-2">
        <div className="border-b border-border bg-success-soft/50 px-5 py-5 sm:border-r sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-success">
            Current Leader
          </p>
          <p className="mt-2 font-display text-2xl font-semibold tracking-tight text-ink">
            {leaderName}
          </p>
          <p className="mt-1 text-sm leading-6 text-secondary">
            Best current candidate based on verified evidence
          </p>
        </div>
        <div className="border-b border-border px-5 py-5 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Confidence
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge variant={confidenceTone(confidence)}>
              {CONFIDENCE_LABEL[confidence]}
            </Badge>
            <span className="text-sm text-secondary">
              Derived from evidence completeness and ownership clarity
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6 px-5 py-5 sm:px-6 sm:py-6">
        <div>
          <h4 className="text-sm font-semibold tracking-tight text-ink">
            Why this candidate currently leads
          </h4>
          <ul className="mt-3 space-y-2.5">
            {recommendation.why_leads.map((item) => (
              <li key={item.text} className="flex items-start gap-2.5 text-sm leading-6 text-ink">
                <span
                  className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success/15 text-success"
                  aria-hidden="true"
                >
                  <Icon name="check" className="h-3 w-3" />
                </span>
                <span className="min-w-0 break-words">{item.text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-card border border-warning/25 bg-warning-soft/60 px-4 py-4">
          <div className="flex items-start gap-3">
            <span
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warning/15 text-warning"
              aria-hidden="true"
            >
              <Icon name="alert" className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <h4 className="text-sm font-semibold tracking-tight text-ink">Main Risk</h4>
              <p className="mt-1.5 text-sm leading-6 text-secondary">
                {recommendation.main_risk.text}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-card border border-ai/25 bg-ai-soft/70 px-4 py-4">
          <div className="flex items-start gap-3">
            <span
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ai/15 text-ai-muted"
              aria-hidden="true"
            >
              <Icon name="spark" className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-semibold tracking-tight text-ink">
                Recommended Interview Focus
              </h4>
              <ul className="mt-3 space-y-2">
                {recommendation.interview_focus.map((item) => (
                  <li
                    key={item.text}
                    className="flex items-start gap-2 text-sm leading-6 text-ink"
                  >
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-ai" aria-hidden="true" />
                    <span className="min-w-0 break-words">{item.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="rounded-card border border-border bg-surface-subtle/80 px-4 py-4">
          <h4 className="text-sm font-semibold tracking-tight text-ink">Alternative Outcome</h4>
          <p className="mt-1.5 text-sm leading-6 text-secondary">
            {recommendation.alternative_outcome.text}
          </p>
        </div>

        <p className="text-xs leading-5 text-muted">
          This is an evidence-based recommendation, not a hiring decision. The employer remains
          the final decision maker.
        </p>
      </div>
    </section>
  );
}

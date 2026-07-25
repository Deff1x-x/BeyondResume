"use client";

import type { AiHiringVerdict } from "@/lib/api/types/ai-hiring-intelligence";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icon, type IconName } from "@/components/ui/icon";
import { SkeletonCard } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import { ApiClientError } from "@/lib/api/error";
import { useAiHiringIntelligenceQuery } from "@/lib/ai-hiring-intelligence/hooks";

const VERDICT_LABELS: Record<AiHiringVerdict, string> = {
  strong_hire: "Strong hire",
  hire: "Hire",
  consider: "Consider",
  insufficient_evidence: "Insufficient evidence",
  do_not_hire: "Do not hire"
};

const VERDICT_DOT_CLASS: Record<AiHiringVerdict, string> = {
  strong_hire: "bg-success",
  hire: "bg-success",
  consider: "bg-warning",
  insufficient_evidence: "bg-muted",
  do_not_hire: "bg-danger"
};

type ListTone = "success" | "warning" | "primary";

const TONE_CLASS: Record<ListTone, string> = {
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  primary: "bg-primary/10 text-primary"
};

export function AiHiringIntelligenceSection({
  candidateId,
  vacancyId,
  enabled
}: Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>) {
  const query = useAiHiringIntelligenceQuery(candidateId, vacancyId, enabled);

  if (query.isLoading) {
    return (
      <div role="status">
        <p className="text-sm text-secondary">Generating AI analysis...</p>
        <SkeletonCard />
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div role="status" className="rounded-card border border-border bg-surface p-6 shadow-card">
        <p className="font-medium text-ink">AI analysis is temporarily unavailable.</p>
        <p className="mt-2 text-sm leading-6 text-secondary">
          {unavailableMessage(query.error)}
        </p>
        <Button
          variant="secondary"
          className="mt-4"
          onClick={() => {
            void query.refetch();
          }}
        >
          <Icon name="refresh" className="h-4 w-4" />
          Try again
        </Button>
      </div>
    );
  }

  const data = query.data;
  const verdict = data.verdict as AiHiringVerdict;

  return (
    <div className="space-y-8">
      <Card aria-labelledby="ai-hiring-intelligence-heading">
        <CardContent className="p-6 sm:p-7">
          <div className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/10"
            >
              <Icon name="spark" className="h-[18px] w-[18px]" />
            </span>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
                AI-generated analysis
              </p>
              <h2
                id="ai-hiring-intelligence-heading"
                className="mt-1.5 text-xl font-semibold tracking-tight text-ink"
              >
                AI Hiring Intelligence
              </h2>
              <p className="mt-1.5 text-sm leading-6 text-secondary">
                Evidence-based hiring decision support for this candidate
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 border-t border-border pt-6 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                AI Recommendation
              </p>
              <p
                className="mt-2.5 flex items-center gap-2.5 text-2xl font-semibold tracking-tight text-ink"
                aria-label={`Recommendation: ${verdictLabel(data.verdict)}`}
              >
                <span
                  aria-hidden="true"
                  className={cn("h-2.5 w-2.5 shrink-0 rounded-full", VERDICT_DOT_CLASS[verdict] ?? "bg-muted")}
                />
                <span aria-hidden="true">{verdictLabel(data.verdict)}</span>
              </p>
            </div>
            <div className="sm:border-l sm:border-border sm:pl-6">
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                Confidence
              </p>
              <p
                className="mt-2.5 text-3xl font-semibold tabular-nums tracking-tight text-ink"
                aria-label={`${data.confidence}% confidence`}
              >
                <span aria-hidden="true">{data.confidence}%</span>
              </p>
              <span
                aria-hidden="true"
                className="mt-3 block h-1.5 w-full overflow-hidden rounded-full bg-surface-subtle"
              >
                <span
                  className="block h-full rounded-full bg-primary"
                  style={{ width: `${Math.min(Math.max(data.confidence, 0), 100)}%` }}
                />
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card aria-labelledby="ai-executive-summary-heading">
        <CardContent className="p-6 sm:p-7">
          <h3
            id="ai-executive-summary-heading"
            className="text-xs font-medium uppercase tracking-[0.12em] text-secondary"
          >
            Executive summary
          </h3>
          <p className="mt-3 whitespace-pre-wrap break-words text-base leading-7 text-ink">
            {data.executive_summary}
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {data.strengths.length > 0 ? (
          <InsightCard title="Strengths" icon="check" tone="success" items={data.strengths} />
        ) : null}
        {data.hiring_risks.length > 0 ? (
          <InsightCard title="Hiring risks" icon="alert" tone="warning" items={data.hiring_risks} />
        ) : null}
        {data.confidence_explanation.length > 0 ? (
          <InsightCard
            title="Confidence"
            icon="gauge"
            tone="primary"
            items={data.confidence_explanation}
          />
        ) : null}
        {data.first_90_days_focus.length > 0 ? (
          <InsightCard
            title="First 90 days"
            icon="arrow-right"
            tone="primary"
            items={data.first_90_days_focus}
          />
        ) : null}
      </div>

      <Card aria-labelledby="ai-next-action-heading">
        <CardContent className="flex gap-4 p-6 sm:p-7">
          <span
            aria-hidden="true"
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary"
          >
            <Icon name="arrow-right" className="h-[18px] w-[18px]" />
          </span>
          <div className="min-w-0">
            <h3
              id="ai-next-action-heading"
              className="text-xs font-medium uppercase tracking-[0.12em] text-secondary"
            >
              Recommended next action
            </h3>
            <p className="mt-2 whitespace-pre-wrap break-words text-base leading-7 text-ink">
              {data.recommended_next_action}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function InsightCard({
  title,
  icon,
  tone,
  items
}: Readonly<{
  title: string;
  icon: IconName;
  tone: ListTone;
  items: string[];
}>) {
  const headingId = `ai-insight-${title.toLowerCase().replaceAll(" ", "-")}`;

  return (
    <Card aria-labelledby={headingId} className="h-full">
      <CardContent className="p-6">
        <div className="flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className={cn(
              "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
              TONE_CLASS[tone]
            )}
          >
            <Icon name={icon} className="h-4 w-4" />
          </span>
          <h3 id={headingId} className="text-sm font-semibold tracking-tight text-ink">
            {title}
          </h3>
        </div>
        <ul className="mt-4 space-y-3.5">
          {items.map((item, index) => (
            <li key={`${index}-${item}`} className="flex gap-3">
              <span
                aria-hidden="true"
                className={cn(
                  "mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                  TONE_CLASS[tone]
                )}
              >
                <Icon name={icon} className="h-3 w-3" strokeWidth={2.2} />
              </span>
              <span className="min-w-0 break-words text-sm leading-6 text-secondary">{item}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function verdictLabel(value: string): string {
  return VERDICT_LABELS[value as AiHiringVerdict] ?? "Evidence review";
}

function unavailableMessage(error: unknown): string {
  if (error instanceof ApiClientError && error.status === 503) {
    return "The AI provider could not generate an analysis right now. Please try again later.";
  }
  return "AI analysis could not be loaded right now. Please try again later.";
}

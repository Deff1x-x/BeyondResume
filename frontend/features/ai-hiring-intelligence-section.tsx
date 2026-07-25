"use client";

import type { AiHiringVerdict } from "@/lib/api/types/ai-hiring-intelligence";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SkeletonCard } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/error";
import { useAiHiringIntelligenceQuery } from "@/lib/ai-hiring-intelligence/hooks";

const VERDICT_LABELS: Record<AiHiringVerdict, string> = {
  strong_hire: "Strong hire",
  hire: "Hire",
  consider: "Consider",
  insufficient_evidence: "Insufficient evidence",
  do_not_hire: "Do not hire"
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
      <div role="status" className="rounded-card border border-border bg-surface p-5">
        <p className="font-medium text-ink">AI analysis is temporarily unavailable.</p>
        <p className="mt-2 text-sm leading-6 text-secondary">
          {unavailableMessage(query.error)}
        </p>
        <Button
          size="sm"
          variant="secondary"
          className="mt-4"
          onClick={() => {
            void query.refetch();
          }}
        >
          Try again
        </Button>
      </div>
    );
  }

  const data = query.data;

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="p-5">
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">
            AI-generated analysis
          </p>
          <h2 className="mt-2 text-lg font-semibold text-ink">AI Hiring Intelligence</h2>
          <p className="mt-1 text-sm text-secondary">
            Evidence-based hiring decision support for this candidate
          </p>

          <div className="mt-4 space-y-1">
            <p className="text-sm font-medium text-primary">{verdictLabel(data.verdict)}</p>
            <p className="text-sm text-secondary">{data.confidence}% confidence</p>
          </div>

          <section className="mt-5" aria-labelledby="ai-executive-summary-heading">
            <h3 id="ai-executive-summary-heading" className="text-sm font-medium text-ink">
              Executive Summary
            </h3>
            <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-secondary">
              {data.executive_summary}
            </p>
          </section>

          <List
            title="Strengths"
            items={data.strengths}
            emptyLabel="No clear strengths identified"
          />
          <List
            title="Hiring Risks"
            items={data.hiring_risks}
            emptyLabel="No significant hiring risks identified"
          />
          <List
            title="Confidence Explanation"
            items={data.confidence_explanation}
            emptyLabel="No confidence explanation provided"
          />
          <List
            title="First 90 Days Focus"
            items={data.first_90_days_focus}
            emptyLabel="No first-90-days focus identified"
          />

          <section className="mt-5 border-t border-border pt-4" aria-labelledby="ai-next-action-heading">
            <h3 id="ai-next-action-heading" className="text-sm font-medium text-ink">
              Recommended Next Action
            </h3>
            <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-secondary">
              {data.recommended_next_action}
            </p>
          </section>
        </CardContent>
      </Card>
    </div>
  );
}

function List({
  title,
  items,
  emptyLabel
}: Readonly<{ title: string; items: string[]; emptyLabel: string }>) {
  return (
    <div className="mt-4">
      <p className="text-sm font-medium text-ink">{title}</p>
      {items.length > 0 ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-secondary">
          {items.map((item, index) => (
            <li key={`${index}-${item}`} className="break-words">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-secondary">{emptyLabel}</p>
      )}
    </div>
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

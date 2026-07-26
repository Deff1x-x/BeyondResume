"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EvidenceIntelligenceFlow } from "@/components/evidence-intelligence-flow";
import { Icon } from "@/components/ui/icon";
import { CompareFlowSteps } from "@/features/employer/compare-flow-chrome";
import { HiringRecommendationCard } from "@/features/employer/hiring-recommendation-card";
import { cn } from "@/lib/cn";
import { ApiClientError } from "@/lib/api/error";
import type { AiCandidateCompareResponse } from "@/lib/api/types/ai-candidate-compare";
import { useAiCandidateCompareMutation } from "@/lib/ai-candidate-compare/hooks";

export type AiCandidateCompareSectionProps = Readonly<{
  vacancyId: string;
  candidateIds: string[];
  candidateNamesById: ReadonlyMap<string, string>;
  enabled?: boolean;
}>;

function unavailableMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "AI candidate comparison is temporarily unavailable. Please try again.";
}

function candidateLabel(
  candidateId: string,
  namesById: ReadonlyMap<string, string>
): string {
  return namesById.get(candidateId)?.trim() || candidateId;
}

function InsightList({
  title,
  items,
  className
}: Readonly<{ title: string; items: Array<{ text: string }>; className?: string }>) {
  if (items.length === 0) {
    return null;
  }
  return (
    <div className={className}>
      <h4 className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
        {title}
      </h4>
      <ul className="mt-2 list-disc space-y-1.5 pl-4 text-sm text-ink">
        {items.map((item) => (
          <li key={item.text} className="break-words leading-6">
            {item.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AiCandidateCompareSection({
  vacancyId,
  candidateIds,
  candidateNamesById,
  enabled = true
}: AiCandidateCompareSectionProps) {
  const mutation = useAiCandidateCompareMutation(vacancyId, candidateIds);
  const [lastSuccess, setLastSuccess] = useState<AiCandidateCompareResponse | null>(null);
  const [revealReady, setRevealReady] = useState(false);
  const selectionValid = enabled && candidateIds.length >= 2 && candidateIds.length <= 4;
  const selectionKey = candidateIds.join(",");

  useEffect(() => {
    setLastSuccess(null);
    setRevealReady(false);
  }, [vacancyId, selectionKey]);

  useEffect(() => {
    if (mutation.isSuccess && mutation.data) {
      setLastSuccess(mutation.data);
      setRevealReady(false);
      const frame = window.requestAnimationFrame(() => setRevealReady(true));
      return () => window.cancelAnimationFrame(frame);
    }
  }, [mutation.data, mutation.isSuccess]);

  const display = mutation.isSuccess && mutation.data ? mutation.data : lastSuccess;
  const showUnavailable = mutation.isError && !mutation.isPending;
  const showLoading = mutation.isPending;
  const flowState = showLoading
    ? "loading"
    : display
      ? "success"
      : showUnavailable
        ? "error"
        : "idle";

  return (
    <section
      id="ai-hiring-analysis"
      className="ai-glow scroll-mt-6 space-y-6 overflow-hidden rounded-card border border-ai/25 bg-surface p-5 shadow-card sm:p-6"
      aria-labelledby="ai-candidate-compare-heading"
    >
      <CompareFlowSteps active="ai" className="shadow-none" />

      <div className="relative flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0 max-w-2xl">
          <div className="flex flex-wrap items-center gap-3">
            <span className="ai-icon-pulse inline-flex h-11 w-11 items-center justify-center rounded-card bg-ai/15 text-ai-muted ring-1 ring-ai/25">
              <Icon name="spark" className="h-[18px] w-[18px]" aria-hidden="true" />
            </span>
            <Badge variant="ai" aria-label="AI analysis">
              AI
            </Badge>
            <h2
              id="ai-candidate-compare-heading"
              className="text-xl font-semibold tracking-tight text-ink sm:text-2xl"
            >
              AI Hiring Analysis
            </h2>
            {display?.generation_mode === "mock" ? (
              <Badge variant="neutral" aria-label="Demo AI">
                Demo AI
              </Badge>
            ) : null}
          </div>
          <p className="mt-3 text-sm leading-6 text-secondary">
            Second opinion from an AI Hiring Manager. Uses deterministic evidence only.
            Does not replace recruiter judgement.
          </p>
          <EvidenceIntelligenceFlow state={flowState} className="mt-5" />
        </div>
        <Button
          type="button"
          variant="primary"
          className="min-h-control shrink-0 whitespace-nowrap px-5 font-semibold"
          disabled={!selectionValid || showLoading}
          onClick={() => {
            if (!selectionValid) {
              return;
            }
            mutation.mutate();
          }}
        >
          <Icon name="spark" className="h-4 w-4 shrink-0" aria-hidden="true" />
          {showLoading ? "Generating…" : "Generate AI comparison"}
        </Button>
      </div>

      {showLoading ? (
        <div className="space-y-3" role="status" aria-live="polite">
          <p className="text-sm font-medium text-ink">Generating AI comparison…</p>
          <p className="text-sm text-secondary">
            Reading match evidence, weighing risks, and drafting interview focus.
          </p>
          <div className="ai-loading-bar" aria-hidden="true" />
          <ol className="grid gap-2 text-xs text-secondary sm:grid-cols-3">
            <li className="rounded-control border border-border bg-surface-subtle/70 px-3 py-2">
              1. Ground in evidence
            </li>
            <li className="rounded-control border border-border bg-surface-subtle/70 px-3 py-2">
              2. Compare trade-offs
            </li>
            <li className="rounded-control border border-border bg-surface-subtle/70 px-3 py-2">
              3. Recommend with caution
            </li>
          </ol>
        </div>
      ) : null}

      {showUnavailable ? (
        <div className="rounded-card border border-border bg-surface-subtle/70 p-5" role="alert">
          <p className="font-medium text-ink">AI comparison is temporarily unavailable.</p>
          <p className="mt-2 text-sm leading-6 text-secondary">
            {unavailableMessage(mutation.error)}
          </p>
          <p className="mt-2 text-sm leading-6 text-secondary">
            The deterministic comparison above remains valid — only the AI second opinion failed.
          </p>
          <Button
            type="button"
            variant="secondary"
            className="mt-4"
            disabled={!selectionValid || showLoading}
            onClick={() => {
              if (!selectionValid) {
                return;
              }
              mutation.mutate();
            }}
          >
            Try again
          </Button>
        </div>
      ) : null}

      {!display && !showLoading && !showUnavailable ? (
        <div className="rounded-card border border-dashed border-ai/30 bg-ai/[0.04] px-5 py-6">
          <p className="text-sm font-medium text-ink">Ready when you are</p>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Generate to surface hiring risks, onboarding insights, and interview focus that are
            not obvious from the comparison table alone. AI Insight builds only after evidence,
            verified skills, and the deterministic match above.
          </p>
        </div>
      ) : null}

      {display ? (
        <div
          className={cn(
            "stagger-children space-y-6 border-t border-border pt-6",
            !revealReady && "opacity-100"
          )}
        >
          <div className="rounded-card border border-border bg-surface-subtle/70 p-5 sm:p-6">
            <h3 className="text-sm font-semibold tracking-tight text-ink">Summary</h3>
            <p className="mt-3 text-sm leading-7 text-ink">{display.summary}</p>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-tight text-ink">Candidate assessments</h3>
            <div className="grid gap-4">
              {display.candidate_assessments.map((assessment) => {
                const name = candidateLabel(assessment.candidate_id, candidateNamesById);
                return (
                  <div
                    key={assessment.candidate_id}
                    className="surface-lift rounded-card border border-border bg-surface p-5"
                    aria-label={`Assessment for ${name}`}
                  >
                    <h4 className="font-medium text-ink">{name}</h4>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2 sm:gap-5">
                      <InsightList title="Strengths" items={assessment.strengths} />
                      <InsightList title="Risks" items={assessment.risks} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-card border border-border bg-background p-5 sm:p-6">
            <InsightList title="Key differences" items={display.key_differences} />
          </div>

          {display.interview_focus_questions.length > 0 ? (
            <div className="rounded-card border border-border bg-surface p-5 sm:p-6">
              <h3 className="text-sm font-semibold tracking-tight text-ink">
                Interview focus questions
              </h3>
              <ol className="mt-4 space-y-4">
                {display.interview_focus_questions.map((item, index) => {
                  const names = item.candidate_ids
                    .map((id) => candidateLabel(id, candidateNamesById))
                    .join(", ");
                  return (
                    <li
                      key={`${item.question}-${names}`}
                      className="flex gap-3 border-t border-border pt-4 first:border-t-0 first:pt-0"
                    >
                      <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ai/15 text-xs font-semibold text-ai-muted">
                        {index + 1}
                      </span>
                      <div>
                        <p className="break-words text-sm leading-6 text-ink">{item.question}</p>
                        <p className="mt-1 text-sm text-secondary">For: {names}</p>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          ) : null}

          <HiringRecommendationCard
            leaderName={candidateLabel(display.recommended_candidate_id, candidateNamesById)}
            confidence={display.confidence}
            recommendation={display.hiring_recommendation}
          />

          <InsightList title="Uncertainties" items={display.uncertainties} />

          <p className="text-xs leading-5 text-muted">
            Advisory only. This comparison must not be treated as an automatic hire/reject
            decision and does not mutate the hiring pipeline.
          </p>
        </div>
      ) : null}
    </section>
  );
}

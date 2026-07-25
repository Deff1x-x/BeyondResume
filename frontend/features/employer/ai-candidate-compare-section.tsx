"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { CompareFlowSteps } from "@/features/employer/compare-flow-chrome";
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
  items
}: Readonly<{ title: string; items: Array<{ text: string }> }>) {
  if (items.length === 0) {
    return null;
  }
  return (
    <div>
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
  const selectionValid = enabled && candidateIds.length >= 2 && candidateIds.length <= 4;
  const selectionKey = candidateIds.join(",");

  useEffect(() => {
    setLastSuccess(null);
  }, [vacancyId, selectionKey]);

  useEffect(() => {
    if (mutation.isSuccess && mutation.data) {
      setLastSuccess(mutation.data);
    }
  }, [mutation.data, mutation.isSuccess]);

  const display = mutation.isSuccess && mutation.data ? mutation.data : lastSuccess;
  const showUnavailable = mutation.isError && !mutation.isPending;
  const showLoading = mutation.isPending;

  return (
    <section
      id="ai-hiring-analysis"
      className="scroll-mt-6 space-y-6 rounded-card border border-border bg-surface p-5 shadow-card sm:p-6"
      aria-labelledby="ai-candidate-compare-heading"
    >
      <CompareFlowSteps active="ai" className="shadow-none" />

      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0 max-w-2xl">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/10">
              <Icon name="spark" className="h-[18px] w-[18px]" aria-hidden="true" />
            </span>
            <Badge variant="accent" aria-label="AI analysis">
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
        <p className="text-sm text-secondary" role="status" aria-live="polite">
          Generating AI comparison…
        </p>
      ) : null}

      {showUnavailable ? (
        <div className="rounded-xl border border-border bg-surface-subtle/70 p-5" role="alert">
          <p className="font-medium text-ink">AI comparison is temporarily unavailable.</p>
          <p className="mt-2 text-sm leading-6 text-secondary">
            {unavailableMessage(mutation.error)}
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
        <div className="rounded-xl border border-dashed border-border bg-surface-subtle/50 px-5 py-6">
          <p className="text-sm font-medium text-ink">Ready when you are</p>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Generate to surface hiring risks, onboarding insights, and interview focus that are
            not obvious from the comparison table alone.
          </p>
        </div>
      ) : null}

      {display ? (
        <div className="space-y-5 border-t border-border pt-6">
          <div className="rounded-xl border border-border bg-surface-subtle/70 p-5">
            <h3 className="text-sm font-semibold tracking-tight text-ink">Summary</h3>
            <p className="mt-3 text-sm leading-6 text-ink">{display.summary}</p>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-tight text-ink">Candidate assessments</h3>
            <div className="grid gap-4">
              {display.candidate_assessments.map((assessment) => {
                const name = candidateLabel(assessment.candidate_id, candidateNamesById);
                return (
                  <div
                    key={assessment.candidate_id}
                    className="rounded-xl border border-border bg-surface p-5"
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

          <InsightList title="Key differences" items={display.key_differences} />

          {display.interview_focus_questions.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold tracking-tight text-ink">Interview focus questions</h3>
              <ul className="list-disc space-y-3 pl-4 text-sm text-ink">
                {display.interview_focus_questions.map((item) => {
                  const names = item.candidate_ids
                    .map((id) => candidateLabel(id, candidateNamesById))
                    .join(", ");
                  return (
                    <li key={`${item.question}-${names}`} className="leading-6">
                      <span className="break-words">{item.question}</span>
                      <span className="mt-1 block text-secondary">For: {names}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          <div className="rounded-xl border border-border bg-surface-subtle/70 p-5">
            <h3 className="text-sm font-semibold tracking-tight text-ink">Recommendation</h3>
            {display.recommended_candidate_id ? (
              <div className="mt-3 space-y-2 text-sm leading-6 text-ink">
                <p className="font-medium">
                  {candidateLabel(display.recommended_candidate_id, candidateNamesById)}
                </p>
                {display.recommendation_rationale ? (
                  <p className="text-secondary">{display.recommendation_rationale.text}</p>
                ) : null}
              </div>
            ) : (
              <p className="mt-3 text-sm leading-6 text-secondary">No clear recommendation</p>
            )}
            <p className="mt-3 text-xs text-muted">
              Confidence: {display.confidence}
            </p>
          </div>

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

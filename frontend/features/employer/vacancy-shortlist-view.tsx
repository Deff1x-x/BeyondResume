"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ActionCard } from "@/components/ui/action-card";
import { Button, primaryActionClass } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { buildCompareHref } from "@/features/employer/candidate-comparison-view";
import {
  CompareFlowSteps,
  CompareValueProps
} from "@/features/employer/compare-flow-chrome";
import { ShortlistNoteEditor } from "@/features/employer/shortlist-note-editor";
import { ShortlistStageControl } from "@/features/employer/shortlist-stage-control";
import { VacancyMatchCard } from "@/features/employer/vacancy-match-card";
import { ApiClientError } from "@/lib/api/error";
import type {
  EmployerCandidateStage,
  VacancyMatch
} from "@/lib/api/types/employer";
import {
  EMPLOYER_CANDIDATE_STAGE_LABELS,
  EMPLOYER_CANDIDATE_STAGES
} from "@/lib/api/types/employer";
import { INTERVIEW_RECOMMENDATION_LABELS } from "@/lib/api/types/interview-scorecard";
import {
  useEmployerVacancyQuery,
  useRemoveCandidateFromShortlist,
  useVacancyMatchesQuery,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

const MAX_COMPARE_SELECTION = 4;
const MIN_COMPARE_SELECTION = 2;

type VacancyShortlistViewProps = Readonly<{
  vacancyId: string;
  enabled: boolean;
}>;

type StageFilter = "all" | EmployerCandidateStage;

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "The shortlist could not be loaded. Please try again.";
}

function fallbackMatch(candidateId: string): VacancyMatch {
  return {
    candidate_id: candidateId,
    candidate_name: "Saved candidate",
    score: 0,
    required: { matched: [], missing: [] },
    preferred: { matched: [], missing: [] }
  };
}

function ShortlistRemoveButton({
  vacancyId,
  candidateId,
  candidateName,
  onRemoved
}: Readonly<{
  vacancyId: string;
  candidateId: string;
  candidateName: string;
  onRemoved?: (candidateId: string) => void;
}>) {
  const removeMutation = useRemoveCandidateFromShortlist(vacancyId);
  const removingThis =
    removeMutation.isPending && removeMutation.variables === candidateId;

  return (
    <>
      <ActionCard
        variant="destructive"
        icon="trash-2"
        title={removingThis ? "Removing..." : "Remove from shortlist"}
        description="Remove candidate from shortlist"
        loading={removingThis}
        disabled={removingThis}
        aria-label={`Remove ${candidateName} from shortlist`}
        onClick={() => {
          if (removingThis) {
            return;
          }
          onRemoved?.(candidateId);
          removeMutation.mutate(candidateId);
        }}
      />
      {removeMutation.isError ? (
        <p className="col-span-full text-sm text-danger" role="alert">
          {errorMessage(removeMutation.error)}
        </p>
      ) : null}
    </>
  );
}

function filterButtonClass(active: boolean): string {
  return `rounded-control px-3 py-2 text-sm font-medium transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 ${
    active
      ? "bg-surface text-ink shadow-sm"
      : "text-secondary hover:bg-surface/80 hover:text-ink"
  }`;
}

export function VacancyShortlistView({ vacancyId, enabled }: VacancyShortlistViewProps) {
  const vacancyQuery = useEmployerVacancyQuery(vacancyId, enabled);
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, enabled);
  const matchesQuery = useVacancyMatchesQuery(vacancyId, enabled);
  const [stageFilter, setStageFilter] = useState<StageFilter>("all");
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);

  const matchesByCandidate = useMemo(() => {
    const map = new Map<string, VacancyMatch>();
    for (const match of matchesQuery.data?.matches ?? []) {
      map.set(match.candidate_id, match);
    }
    return map;
  }, [matchesQuery.data?.matches]);

  const entries = shortlistQuery.data?.entries ?? [];
  const shortlistMembershipKey = useMemo(
    () =>
      (shortlistQuery.data?.entries ?? [])
        .map((entry) => entry.candidate_id)
        .join("\u0001"),
    [shortlistQuery.data?.entries]
  );

  useEffect(() => {
    const validIds = new Set(
      shortlistMembershipKey === "" ? [] : shortlistMembershipKey.split("\u0001")
    );
    setSelectedCandidateIds((current) => {
      const next = current.filter((id) => validIds.has(id));
      if (next.length === current.length) {
        return current;
      }
      return next;
    });
  }, [shortlistMembershipKey]);

  const visibleEntries =
    stageFilter === "all"
      ? entries
      : entries.filter((entry) => entry.stage === stageFilter);
  const selectionCount = selectedCandidateIds.length;
  const selectionAtMax = selectionCount >= MAX_COMPARE_SELECTION;
  const canCompare = selectionCount >= MIN_COMPARE_SELECTION && selectionCount <= MAX_COMPARE_SELECTION;
  const compareHref = buildCompareHref(vacancyId, selectedCandidateIds);
  const backHref = "/#employer-vacancies";
  const breadcrumb = (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2">
      <Link href={backHref} className="app-link">
        Employer dashboard
      </Link>
      <span aria-hidden="true" className="text-muted">
        /
      </span>
      <span className="text-secondary">Shortlist</span>
    </nav>
  );

  function toggleCompareSelection(candidateId: string) {
    setSelectedCandidateIds((current) => {
      if (current.includes(candidateId)) {
        return current.filter((id) => id !== candidateId);
      }
      if (current.length >= MAX_COMPARE_SELECTION) {
        return current;
      }
      return [...current, candidateId];
    });
  }

  function removeFromSelection(candidateId: string) {
    setSelectedCandidateIds((current) =>
      current.includes(candidateId)
        ? current.filter((id) => id !== candidateId)
        : current
    );
  }

  if (!enabled) {
    return (
      <EmptyState
        title="Employer access required"
        description="Shortlists are available only to employer accounts."
      />
    );
  }

  if (vacancyQuery.isLoading || shortlistQuery.isLoading || matchesQuery.isLoading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Shortlist" breadcrumb={breadcrumb} />
        <div role="status" aria-label="Loading shortlist" className="space-y-5">
          <SkeletonCard className="min-h-24" />
          <SkeletonListRow />
          <SkeletonCard className="min-h-48" />
          <SkeletonCard className="min-h-48" />
        </div>
      </div>
    );
  }

  if (vacancyQuery.isError || shortlistQuery.isError) {
    return (
      <div className="space-y-8">
        <PageHeader title="Shortlist" breadcrumb={breadcrumb} />
        <EmptyState
          role="alert"
          title="Shortlist unavailable"
          description={errorMessage(vacancyQuery.error ?? shortlistQuery.error)}
          className="py-10"
          primaryAction={
            <Button
              variant="secondary"
              onClick={() => {
                void vacancyQuery.refetch();
                void shortlistQuery.refetch();
                void matchesQuery.refetch();
              }}
            >
              Try again
            </Button>
          }
          secondaryAction={breadcrumb}
        />
      </div>
    );
  }

  const vacancyTitle = vacancyQuery.data?.title ?? "Vacancy";
  const selectionHint =
    selectionCount < MIN_COMPARE_SELECTION
      ? `Select ${MIN_COMPARE_SELECTION - selectionCount} more to compare`
      : selectionAtMax
        ? `Maximum ${MAX_COMPARE_SELECTION} candidates selected`
        : `${selectionCount} of up to ${MAX_COMPARE_SELECTION} selected`;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Hiring workspace"
        title="Select candidates to compare"
        description={`Choose 2–4 shortlisted people for ${vacancyTitle}. Next you will get a side-by-side match table and AI Hiring Analysis.`}
        breadcrumb={breadcrumb}
      />

      <CompareFlowSteps active="select" />

      {matchesQuery.isError ? (
        <p className="text-sm text-danger" role="alert">
          Match details could not be loaded for saved candidates.
        </p>
      ) : null}

      {entries.length > 0 ? (
        <section
          className="space-y-5 rounded-card border border-border bg-surface p-5 shadow-card sm:p-6"
          aria-labelledby="compare-value-heading"
        >
          <SectionHeader
            titleId="compare-value-heading"
            title="What you will get"
            description="Comparison is not just a table — it prepares a hiring decision workspace."
            size="md"
          />
          <CompareValueProps />
        </section>
      ) : null}

      {entries.length > 0 ? (
        <section className="space-y-5" aria-labelledby="shortlist-candidates-heading">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-6">
            <SectionHeader
              titleId="shortlist-candidates-heading"
              title="Shortlisted candidates"
              description="Select cards to build a compare set, then continue from the bar below."
              size="md"
              count={
                <span className="text-sm text-secondary">
                  {visibleEntries.length} shown
                </span>
              }
            />
            <div
              className="flex w-fit max-w-full flex-wrap rounded-card border border-border bg-surface-subtle p-1"
              role="group"
              aria-label="Filter shortlist by hiring stage"
            >
              <button
                type="button"
                aria-pressed={stageFilter === "all"}
                className={filterButtonClass(stageFilter === "all")}
                onClick={() => setStageFilter("all")}
              >
                All
              </button>
              {EMPLOYER_CANDIDATE_STAGES.map((stage) => (
                <button
                  key={stage}
                  type="button"
                  aria-pressed={stageFilter === stage}
                  className={filterButtonClass(stageFilter === stage)}
                  onClick={() => setStageFilter(stage)}
                >
                  {EMPLOYER_CANDIDATE_STAGE_LABELS[stage]}
                </button>
              ))}
            </div>
          </div>

          <div className="sticky top-3 z-20 rounded-card border border-border bg-surface p-5 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink" aria-live="polite">
                  {selectionCount} selected
                </p>
                <p className="mt-1 text-sm leading-6 text-secondary">{selectionHint}</p>
              </div>
              {canCompare ? (
                <Link
                  href={compareHref}
                  className={primaryActionClass}
                  aria-label="Compare selected candidates"
                >
                  Compare selected
                  <Icon name="arrow-right" className="h-4 w-4" aria-hidden="true" />
                </Link>
              ) : (
                <Button
                  type="button"
                  variant="primary"
                  className="min-h-control px-5 font-semibold"
                  disabled
                  aria-label="Compare selected candidates"
                >
                  Compare selected
                </Button>
              )}
            </div>
            {canCompare ? (
              <p className="mt-3 text-xs leading-5 text-muted">
                Continues to deterministic comparison and AI Hiring Analysis for the selected
                candidates.
              </p>
            ) : null}
          </div>

          {visibleEntries.length === 0 && stageFilter !== "all" ? (
            <EmptyState
              title={`No candidates in ${EMPLOYER_CANDIDATE_STAGE_LABELS[stageFilter]}.`}
              description="Choose another stage filter or move a saved candidate into this stage."
              className="bg-surface py-10"
            />
          ) : null}

          {visibleEntries.length > 0 ? (
            <ul className="space-y-5">
              {visibleEntries.map((entry) => {
                const match =
                  matchesByCandidate.get(entry.candidate_id) ??
                  fallbackMatch(entry.candidate_id);
                const selected = selectedCandidateIds.includes(entry.candidate_id);
                const checkboxDisabled = selectionAtMax && !selected;
                return (
                  <VacancyMatchCard
                    key={entry.id}
                    match={match}
                    vacancyId={vacancyId}
                    saved
                    selected={selected}
                    stage={entry.stage}
                    reviewVariant="secondary"
                    selection={{
                      checked: selected,
                      disabled: checkboxDisabled,
                      onChange: () => toggleCompareSelection(entry.candidate_id)
                    }}
                    pipelineActions={
                      <>
                        <div className="col-span-full">
                          <ShortlistStageControl
                            vacancyId={vacancyId}
                            candidateId={entry.candidate_id}
                            stage={entry.stage}
                            candidateLabel={match.candidate_name}
                            compact
                          />
                        </div>
                        <ActionCard
                          href={`/employer/matches/${encodeURIComponent(entry.candidate_id)}/interview-questions?vacancy_id=${encodeURIComponent(vacancyId)}`}
                          icon="message-square-question"
                          iconTone="ai"
                          title="Interview questions"
                          description="AI-generated interview plan"
                        />
                        <ActionCard
                          href={`/employer/matches/${encodeURIComponent(entry.candidate_id)}/scorecard?vacancy_id=${encodeURIComponent(vacancyId)}`}
                          icon="clipboard-check"
                          iconTone="primary"
                          title={
                            entry.scorecard_status === "completed"
                              ? "Open scorecard"
                              : entry.scorecard_status === "draft"
                                ? "Continue scorecard draft"
                                : "Open interview scorecard"
                          }
                          description="Evaluate interview"
                        />
                        <ShortlistRemoveButton
                          vacancyId={vacancyId}
                          candidateId={entry.candidate_id}
                          candidateName={match.candidate_name}
                          onRemoved={removeFromSelection}
                        />
                      </>
                    }
                    notes={
                      <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="neutral">
                            Scorecard:{" "}
                            {entry.scorecard_status === "completed"
                              ? "Completed"
                              : entry.scorecard_status === "draft"
                                ? "Draft"
                                : "Not started"}
                          </Badge>
                          {entry.scorecard_recommendation ? (
                            <Badge variant="primary">
                              {INTERVIEW_RECOMMENDATION_LABELS[entry.scorecard_recommendation]}
                            </Badge>
                          ) : null}
                        </div>
                        <ShortlistNoteEditor
                          vacancyId={vacancyId}
                          candidateId={entry.candidate_id}
                          note={entry.note}
                          candidateLabel={match.candidate_name}
                        />
                      </div>
                    }
                  />
                );
              })}
            </ul>
          ) : null}
        </section>
      ) : null}

      {entries.length === 0 ? (
        <EmptyState
          title="No candidates shortlisted yet."
          description="Add candidates from Applicants or Recommended before starting AI comparison."
          className="bg-surface py-10"
        />
      ) : null}
    </div>
  );
}

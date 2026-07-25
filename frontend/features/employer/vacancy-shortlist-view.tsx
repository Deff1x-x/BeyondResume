"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { buildCompareHref } from "@/features/employer/candidate-comparison-view";
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
    <div className="space-y-2">
      <Button
        type="button"
        variant="secondary"
        size="sm"
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
      >
        {removingThis ? "Removing..." : "Remove"}
      </Button>
      {removeMutation.isError ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(removeMutation.error)}
        </p>
      ) : null}
    </div>
  );
}

function filterButtonClass(active: boolean): string {
  return `rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 ${
    active
      ? "bg-background text-ink shadow-sm"
      : "text-secondary hover:bg-background/70 hover:text-ink"
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
        <div role="status" aria-label="Loading shortlist" className="space-y-4">
          <SkeletonListRow />
          <SkeletonCard className="min-h-40" />
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

  return (
    <div className="space-y-8">
      <PageHeader
        title="Shortlist"
        description={`Saved candidates for ${vacancyTitle}.`}
        breadcrumb={breadcrumb}
      />

      {matchesQuery.isError ? (
        <p className="text-sm text-danger" role="alert">
          Match details could not be loaded for saved candidates.
        </p>
      ) : null}

      {entries.length > 0 ? (
        <div
          className="flex w-fit max-w-full flex-wrap rounded-xl border border-border bg-surface-subtle p-1"
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
      ) : null}

      {entries.length === 0 ? (
        <EmptyState
          title="No saved candidates yet."
          description="Save a candidate from Candidate Review to see them here."
          className="py-8"
        />
      ) : null}

      {entries.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-surface-subtle/60 px-4 py-3">
          <p className="text-sm text-secondary" aria-live="polite">
            {selectionCount} selected
          </p>
          {canCompare ? (
            <Link
              href={compareHref}
              className="inline-flex min-h-control items-center rounded-button border border-primary bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
              aria-label="Compare selected candidates"
            >
              Compare selected
            </Link>
          ) : (
            <Button
              type="button"
              variant="primary"
              disabled
              aria-label="Compare selected candidates"
            >
              Compare selected
            </Button>
          )}
        </div>
      ) : null}

      {entries.length > 0 && visibleEntries.length === 0 && stageFilter !== "all" ? (
        <EmptyState
          title={`No candidates in ${EMPLOYER_CANDIDATE_STAGE_LABELS[stageFilter]}.`}
          description="Choose another stage filter or move a saved candidate into this stage."
          className="py-8"
        />
      ) : null}

      {visibleEntries.length > 0 ? (
        <ul className="space-y-3">
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
                actions={
                  <div className="w-full space-y-4 sm:w-auto">
                    <label className="flex items-center gap-2 text-sm text-ink">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-border text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                        checked={selected}
                        disabled={checkboxDisabled}
                        aria-label={`Select ${match.candidate_name} for comparison`}
                        onChange={() => toggleCompareSelection(entry.candidate_id)}
                      />
                      <span>Compare</span>
                    </label>
                    <div className="flex w-full flex-wrap items-start gap-3 sm:w-auto">
                      <ShortlistStageControl
                        vacancyId={vacancyId}
                        candidateId={entry.candidate_id}
                        stage={entry.stage}
                        candidateLabel={match.candidate_name}
                      />
                      <ShortlistRemoveButton
                        vacancyId={vacancyId}
                        candidateId={entry.candidate_id}
                        candidateName={match.candidate_name}
                        onRemoved={removeFromSelection}
                      />
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
    </div>
  );
}

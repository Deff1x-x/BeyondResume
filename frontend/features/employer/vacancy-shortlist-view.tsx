"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { VacancyMatchCard } from "@/features/employer/vacancy-match-card";
import { ApiClientError } from "@/lib/api/error";
import type { VacancyMatch } from "@/lib/api/types/employer";
import {
  useEmployerVacancyQuery,
  useRemoveCandidateFromShortlist,
  useVacancyMatchesQuery,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

type VacancyShortlistViewProps = Readonly<{
  vacancyId: string;
  enabled: boolean;
}>;

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
  candidateName
}: Readonly<{ vacancyId: string; candidateId: string; candidateName: string }>) {
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

export function VacancyShortlistView({ vacancyId, enabled }: VacancyShortlistViewProps) {
  const vacancyQuery = useEmployerVacancyQuery(vacancyId, enabled);
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, enabled);
  const matchesQuery = useVacancyMatchesQuery(vacancyId, enabled);

  const matchesByCandidate = useMemo(() => {
    const map = new Map<string, VacancyMatch>();
    for (const match of matchesQuery.data?.matches ?? []) {
      map.set(match.candidate_id, match);
    }
    return map;
  }, [matchesQuery.data?.matches]);

  const entries = shortlistQuery.data?.entries ?? [];
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

      {entries.length === 0 ? (
        <EmptyState
          title="No saved candidates yet."
          description="Save a candidate from Candidate Review to see them here."
          className="py-8"
        />
      ) : (
        <ul className="space-y-3">
          {entries.map((entry) => {
            const match =
              matchesByCandidate.get(entry.candidate_id) ??
              fallbackMatch(entry.candidate_id);
            return (
              <VacancyMatchCard
                key={entry.id}
                match={match}
                vacancyId={vacancyId}
                saved
                actions={
                  <ShortlistRemoveButton
                    vacancyId={vacancyId}
                    candidateId={entry.candidate_id}
                    candidateName={match.candidate_name}
                  />
                }
              />
            );
          })}
        </ul>
      )}
    </div>
  );
}

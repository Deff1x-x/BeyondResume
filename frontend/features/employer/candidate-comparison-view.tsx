"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/error";
import type {
  EmployerShortlistEntry,
  VacancyMatch
} from "@/lib/api/types/employer";
import { EMPLOYER_CANDIDATE_STAGE_LABELS } from "@/lib/api/types/employer";
import {
  useVacancyMatchesQuery,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

const MAX_COMPARE_CANDIDATES = 4;
const MIN_COMPARE_CANDIDATES = 2;

export type CandidateComparisonViewProps = Readonly<{
  vacancyId: string;
  selectedCandidateIds: string[];
  enabled?: boolean;
}>;

type ComparisonRow = {
  candidateId: string;
  entry: EmployerShortlistEntry;
  match: VacancyMatch | null;
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Candidate comparison could not be loaded. Please try again.";
}

function stageBadgeVariant(
  stage: EmployerShortlistEntry["stage"]
): "neutral" | "success" | "danger" {
  if (stage === "hired") {
    return "success";
  }
  if (stage === "rejected") {
    return "danger";
  }
  return "neutral";
}

/** Deduplicate IDs while preserving first-seen order. Trims empty segments. */
export function parseCompareCandidateIds(idsParam: string | null | undefined): string[] {
  if (!idsParam) {
    return [];
  }
  const result: string[] = [];
  const seen = new Set<string>();
  for (const part of idsParam.split(",")) {
    const id = part.trim();
    if (!id || seen.has(id)) {
      continue;
    }
    seen.add(id);
    result.push(id);
  }
  return result;
}

export function buildCompareHref(vacancyId: string, candidateIds: string[]): string {
  const uniqueIds = parseCompareCandidateIds(candidateIds.join(","));
  const encodedIds = uniqueIds.map((id) => encodeURIComponent(id)).join(",");
  return `/employer/vacancies/${encodeURIComponent(vacancyId)}/compare?ids=${encodedIds}`;
}

function formatNote(note: string | null): string {
  if (note === null || note.trim() === "") {
    return "No private note";
  }
  return note;
}

function SkillList({
  skills,
  unavailable
}: Readonly<{ skills: string[] | null; unavailable?: boolean }>) {
  if (unavailable) {
    return <p className="text-sm text-secondary">Unavailable</p>;
  }
  if (skills === null || skills.length === 0) {
    return <p className="text-sm text-secondary">None</p>;
  }
  return (
    <ul className="list-disc space-y-1 pl-4 text-sm text-ink">
      {skills.map((skill) => (
        <li key={skill} className="break-words">
          {skill}
        </li>
      ))}
    </ul>
  );
}

export function CandidateComparisonView({
  vacancyId,
  selectedCandidateIds,
  enabled = true
}: CandidateComparisonViewProps) {
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, enabled);
  const matchesQuery = useVacancyMatchesQuery(vacancyId, enabled);
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;

  const breadcrumb = (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2">
      <Link href={shortlistHref} className="app-link">
        Shortlist
      </Link>
      <span aria-hidden="true" className="text-muted">
        /
      </span>
      <span className="text-secondary">Compare</span>
    </nav>
  );

  const matchesByCandidate = useMemo(() => {
    const map = new Map<string, VacancyMatch>();
    for (const match of matchesQuery.data?.matches ?? []) {
      map.set(match.candidate_id, match);
    }
    return map;
  }, [matchesQuery.data?.matches]);

  const shortlistByCandidate = useMemo(() => {
    const map = new Map<string, EmployerShortlistEntry>();
    for (const entry of shortlistQuery.data?.entries ?? []) {
      map.set(entry.candidate_id, entry);
    }
    return map;
  }, [shortlistQuery.data?.entries]);

  const { rows, truncated } = useMemo(() => {
    const seen = new Set<string>();
    const validOrdered: string[] = [];
    for (const id of selectedCandidateIds) {
      if (!id || seen.has(id) || !shortlistByCandidate.has(id)) {
        continue;
      }
      seen.add(id);
      validOrdered.push(id);
    }
    const limited = validOrdered.slice(0, MAX_COMPARE_CANDIDATES);
    const nextRows: ComparisonRow[] = [];
    for (const candidateId of limited) {
      const entry = shortlistByCandidate.get(candidateId);
      if (!entry) {
        continue;
      }
      nextRows.push({
        candidateId,
        entry,
        match: matchesByCandidate.get(candidateId) ?? null
      });
    }
    return {
      rows: nextRows,
      truncated: validOrdered.length > MAX_COMPARE_CANDIDATES
    };
  }, [matchesByCandidate, selectedCandidateIds, shortlistByCandidate]);

  if (!enabled) {
    return (
      <EmptyState
        title="Employer access required"
        description="Candidate comparison is available only to employer accounts."
      />
    );
  }

  if (shortlistQuery.isLoading || matchesQuery.isLoading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Compare candidates" breadcrumb={breadcrumb} />
        <div role="status" aria-label="Loading candidate comparison" className="space-y-4">
          <SkeletonListRow />
          <SkeletonCard className="min-h-40" />
        </div>
      </div>
    );
  }

  if (shortlistQuery.isError || matchesQuery.isError) {
    return (
      <div className="space-y-8">
        <PageHeader title="Compare candidates" breadcrumb={breadcrumb} />
        <EmptyState
          role="alert"
          title="Comparison unavailable"
          description={errorMessage(shortlistQuery.error ?? matchesQuery.error)}
          primaryAction={
            <Button
              variant="secondary"
              onClick={() => {
                void shortlistQuery.refetch();
                void matchesQuery.refetch();
              }}
            >
              Try again
            </Button>
          }
          secondaryAction={
            <Link href={shortlistHref} className="app-link">
              Back to shortlist
            </Link>
          }
        />
      </div>
    );
  }

  if (rows.length < MIN_COMPARE_CANDIDATES) {
    return (
      <div className="space-y-8">
        <PageHeader title="Compare candidates" breadcrumb={breadcrumb} />
        <EmptyState
          title="Select at least two shortlisted candidates to compare."
          description="Choose candidates from this vacancy shortlist, then open Compare selected."
          primaryAction={
            <Link
              href={shortlistHref}
              className="inline-flex min-h-control items-center rounded-button border border-primary bg-primary px-4 text-sm font-medium text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Back to shortlist
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Compare candidates"
        description="Side-by-side comparison of shortlisted candidates for this vacancy."
        breadcrumb={breadcrumb}
      />

      {truncated ? (
        <p className="text-sm text-secondary" role="status">
          Only the first four shortlisted candidates are shown.
        </p>
      ) : null}

      <div
        className="overflow-x-auto rounded-xl border border-border"
        role="region"
        aria-label="Candidate comparison table"
        tabIndex={0}
      >
        <table className="min-w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border bg-surface-subtle/70">
              <th
                scope="col"
                className="sticky left-0 z-10 min-w-[9rem] bg-surface-subtle/95 px-4 py-3 text-sm font-semibold text-secondary backdrop-blur-sm"
              >
                Criteria
              </th>
              {rows.map((row) => {
                const name = row.match?.candidate_name?.trim() || row.candidateId;
                return (
                  <th
                    key={row.candidateId}
                    scope="col"
                    className="min-w-[14rem] max-w-[18rem] border-l border-border px-4 py-3 align-bottom"
                  >
                    <h2 className="break-words text-base font-semibold text-ink">{name}</h2>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Match score
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-score`}
                  className="border-l border-border px-4 py-3 text-sm text-ink"
                >
                  {row.match ? (
                    <span className="text-lg font-semibold tabular-nums">{row.match.score}%</span>
                  ) : (
                    <span className="text-secondary">Unavailable</span>
                  )}
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Required skills matched
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-req-matched`}
                  className="border-l border-border px-4 py-3"
                >
                  <SkillList
                    skills={row.match?.required.matched ?? null}
                    unavailable={!row.match}
                  />
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Required skills missing
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-req-missing`}
                  className="border-l border-border px-4 py-3"
                >
                  <SkillList
                    skills={row.match?.required.missing ?? null}
                    unavailable={!row.match}
                  />
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Preferred skills matched
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-pref-matched`}
                  className="border-l border-border px-4 py-3"
                >
                  <SkillList
                    skills={row.match?.preferred.matched ?? null}
                    unavailable={!row.match}
                  />
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Preferred skills missing
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-pref-missing`}
                  className="border-l border-border px-4 py-3"
                >
                  <SkillList
                    skills={row.match?.preferred.missing ?? null}
                    unavailable={!row.match}
                  />
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Pipeline stage
              </th>
              {rows.map((row) => (
                <td
                  key={`${row.candidateId}-stage`}
                  className="border-l border-border px-4 py-3"
                >
                  <Badge variant={stageBadgeVariant(row.entry.stage)}>
                    {EMPLOYER_CANDIDATE_STAGE_LABELS[row.entry.stage]}
                  </Badge>
                </td>
              ))}
            </tr>

            <tr className="border-b border-border align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Private note
              </th>
              {rows.map((row) => {
                const noteText = formatNote(row.entry.note);
                const hasNote = Boolean(row.entry.note?.trim());
                return (
                  <td
                    key={`${row.candidateId}-note`}
                    className="max-w-[18rem] border-l border-border px-4 py-3"
                  >
                    <p
                      className={`whitespace-pre-wrap break-words text-sm ${
                        hasNote ? "text-ink" : "text-secondary"
                      }`}
                    >
                      {noteText}
                    </p>
                  </td>
                );
              })}
            </tr>

            <tr className="align-top">
              <th
                scope="row"
                className="sticky left-0 z-10 bg-background px-4 py-3 text-sm font-medium text-secondary"
              >
                Candidate Review
              </th>
              {rows.map((row) => {
                const name = row.match?.candidate_name?.trim() || row.candidateId;
                const href = `/employer/matches/${encodeURIComponent(row.candidateId)}?vacancy_id=${encodeURIComponent(vacancyId)}`;
                return (
                  <td
                    key={`${row.candidateId}-review`}
                    className="border-l border-border px-4 py-3"
                  >
                    <Link
                      href={href}
                      className="app-link text-sm font-medium"
                      aria-label={`Open Candidate Review for ${name}`}
                    >
                      Open Candidate Review
                    </Link>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";

import { CandidateSummaryCard } from "@/features/match-details/candidate-summary-card";
import { EvidenceCard } from "@/features/match-details/evidence-card";
import { RoadmapCard } from "@/features/match-details/roadmap-card";
import { SkillsComparisonCard } from "@/features/match-details/skills-comparison-card";
import { ApiClientError } from "@/lib/api/error";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";

type CandidateProfileViewProps = Readonly<{
  candidateId: string;
  vacancyId: string;
  enabled: boolean;
}>;

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Match details could not be loaded. Please try again.";
}

export function CandidateProfileView({
  candidateId,
  vacancyId,
  enabled
}: CandidateProfileViewProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);

  if (!enabled) {
    return (
      <p className="text-sm text-secondary" role="status">
        Match details are available only to employer accounts.
      </p>
    );
  }

  if (detailsQuery.isLoading) {
    return (
      <p className="text-sm text-secondary" role="status">
        Loading candidate profile…
      </p>
    );
  }

  if (detailsQuery.isError || !detailsQuery.data) {
    return (
      <div>
        <p className="text-sm text-danger" role="alert">
          {errorMessage(detailsQuery.error)}
        </p>
        <button
          type="button"
          onClick={() => void detailsQuery.refetch()}
          className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Try again
        </button>
      </div>
    );
  }

  const details = detailsQuery.data;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          href="/"
          className="inline-flex min-h-control items-center text-sm font-medium text-primary underline-offset-2 hover:underline"
        >
          ← Back to employer workspace
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,35%)_minmax(0,65%)]">
        <CandidateSummaryCard
          candidate={details.candidate}
          score={details.match.score}
          passport={details.passport}
        />

        <div className="space-y-6">
          <SkillsComparisonCard
            title="Required skills"
            headingId="required-skills-title"
            group={details.match.required}
          />
          <SkillsComparisonCard
            title="Preferred skills"
            headingId="preferred-skills-title"
            group={details.match.preferred}
          />
          <EvidenceCard evidence={details.evidence} />
          <RoadmapCard items={details.roadmap} />
        </div>
      </div>
    </div>
  );
}

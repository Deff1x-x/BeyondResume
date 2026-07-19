"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
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

function MatchDetailsSkeleton() {
  return (
    <div
      className="grid gap-8 lg:grid-cols-[minmax(0,35%)_minmax(0,65%)]"
      role="status"
      aria-label="Loading candidate profile"
    >
      <SkeletonCard className="min-h-64" />
      <div className="space-y-4">
        <SkeletonListRow />
        <SkeletonListRow />
        <SkeletonListRow />
      </div>
    </div>
  );
}

export function CandidateProfileView({
  candidateId,
  vacancyId,
  enabled
}: CandidateProfileViewProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);

  if (!enabled) {
    return (
      <EmptyState
        title="Employer access required"
        description="Match details are available only to employer accounts."
      />
    );
  }

  if (detailsQuery.isLoading) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Candidate profile"
          description="Loading match details…"
          breadcrumb={
            <Link
              href="/"
              className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              ← Back to employer workspace
            </Link>
          }
        />
        <MatchDetailsSkeleton />
      </div>
    );
  }

  if (detailsQuery.isError || !detailsQuery.data) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Candidate profile"
          breadcrumb={
            <Link
              href="/"
              className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              ← Back to employer workspace
            </Link>
          }
        />
        <EmptyState
          role="alert"
          title="Could not load match details"
          description={errorMessage(detailsQuery.error)}
          primaryAction={
            <Button type="button" variant="secondary" onClick={() => void detailsQuery.refetch()}>
              Try again
            </Button>
          }
        />
      </div>
    );
  }

  const details = detailsQuery.data;

  return (
    <div className="space-y-8">
      <PageHeader
        title={details.candidate.name}
        description={
          details.candidate.headline?.trim()
            ? details.candidate.headline
            : "Candidate match profile for this vacancy."
        }
        breadcrumb={
          <Link
            href="/"
            className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
          >
            ← Back to employer workspace
          </Link>
        }
        titleId="candidate-profile-title"
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,35%)_minmax(0,65%)] lg:gap-8">
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

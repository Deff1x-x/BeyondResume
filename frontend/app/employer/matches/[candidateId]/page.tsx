"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import { useCurrentUser } from "@/lib/auth/hooks";
import { getAccessToken } from "@/lib/auth/token";

function MatchDetailsContent() {
  const router = useRouter();
  const params = useParams<{ candidateId: string }>();
  const searchParams = useSearchParams();
  const { data: user, isLoading, isError } = useCurrentUser();

  const candidateId = typeof params.candidateId === "string" ? params.candidateId : "";
  const vacancyId = searchParams.get("vacancy_id");

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!user && getAccessToken() === null) {
      router.replace("/login");
    }
  }, [isLoading, router, user]);

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading account" className="space-y-3">
        <SkeletonText className="h-4 w-28" />
        <SkeletonText className="h-8 w-56" />
      </div>
    );
  }

  if (!user) {
    return (
      <EmptyState
        role="alert"
        title={isError ? "Session unavailable" : "Sign in required"}
        description={
          isError
            ? "We could not verify your session. Sign in to continue."
            : "Sign in to view candidate profiles."
        }
        primaryAction={
          <Link
            href="/login"
            className="inline-flex min-h-control items-center rounded-button border border-primary bg-primary px-4 text-sm font-medium text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
          >
            Go to login
          </Link>
        }
      />
    );
  }

  if (user.role !== "employer") {
    return (
      <EmptyState
        title="Employer access required"
        description="Candidate profiles are available only to employer accounts."
        primaryAction={
          <Link
            href="/"
            className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
          >
            Back to workspace
          </Link>
        }
      />
    );
  }

  if (!candidateId || !vacancyId) {
    return (
      <EmptyState
        role="alert"
        title="Missing match context"
        description="A candidate and vacancy are required to open this profile."
        primaryAction={
          <Link
            href="/"
            className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
          >
            Back to employer workspace
          </Link>
        }
      />
    );
  }

  return <CandidateProfileView candidateId={candidateId} vacancyId={vacancyId} enabled />;
}

export default function EmployerMatchDetailsPage() {
  return (
    <WorkspaceShell role="employer">
      <Suspense
        fallback={
          <div role="status" aria-label="Loading candidate profile" className="space-y-3">
            <SkeletonText className="h-4 w-40" />
            <SkeletonText className="h-8 w-64" />
          </div>
        }
      >
        <MatchDetailsContent />
      </Suspense>
    </WorkspaceShell>
  );
}

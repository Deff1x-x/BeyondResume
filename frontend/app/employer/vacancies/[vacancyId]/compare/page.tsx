"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import {
  CandidateComparisonView,
  parseCompareCandidateIds
} from "@/features/employer/candidate-comparison-view";
import { useCurrentUser } from "@/lib/auth/hooks";
import { getAccessToken } from "@/lib/auth/token";

function CandidateComparisonContent() {
  const router = useRouter();
  const params = useParams<{ vacancyId: string }>();
  const searchParams = useSearchParams();
  const { data: user, isLoading, isError } = useCurrentUser();
  const vacancyId = typeof params.vacancyId === "string" ? params.vacancyId : "";
  const idsParam = searchParams.get("ids");
  const selectedCandidateIds = useMemo(
    () => parseCompareCandidateIds(idsParam),
    [idsParam]
  );

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
            : "Sign in to compare shortlisted candidates."
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
        description="Candidate comparison is available only to employer accounts."
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

  if (!vacancyId) {
    return (
      <EmptyState
        role="alert"
        title="Missing vacancy"
        description="A vacancy is required to compare shortlisted candidates."
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

  return (
    <CandidateComparisonView
      vacancyId={vacancyId}
      selectedCandidateIds={selectedCandidateIds}
      enabled
    />
  );
}

export default function EmployerVacancyComparePage() {
  return (
    <WorkspaceShell role="employer">
      <Suspense
        fallback={
          <div role="status" aria-label="Loading comparison" className="space-y-3">
            <SkeletonText className="h-4 w-28" />
            <SkeletonText className="h-8 w-56" />
          </div>
        }
      >
        <CandidateComparisonContent />
      </Suspense>
    </WorkspaceShell>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageContainer } from "@/components/ui/page-container";
import { SkeletonText } from "@/components/ui/skeleton";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import { useCurrentUser, useLogout } from "@/lib/auth/hooks";
import { getAccessToken } from "@/lib/auth/token";

function MatchDetailsContent() {
  const router = useRouter();
  const params = useParams<{ candidateId: string }>();
  const searchParams = useSearchParams();
  const logout = useLogout();
  const { data: user, isLoading, isError } = useCurrentUser();

  const candidateId = typeof params.candidateId === "string" ? params.candidateId : "";
  const vacancyId = searchParams.get("vacancy_id");
  const hasToken = typeof window !== "undefined" && getAccessToken() !== null;

  useEffect(() => {
    if (!isLoading && !user && !hasToken) {
      router.replace("/login");
    }
  }, [hasToken, isLoading, router, user]);

  function onSignOutClick() {
    logout();
    router.push("/login");
  }

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

  return (
    <>
      <div className="mb-6 flex justify-end border-b border-border pb-4">
        <Button type="button" variant="secondary" onClick={onSignOutClick}>
          Logout
        </Button>
      </div>

      <CandidateProfileView candidateId={candidateId} vacancyId={vacancyId} enabled />
    </>
  );
}

export default function EmployerMatchDetailsPage() {
  return (
    <PageContainer>
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
    </PageContainer>
  );
}

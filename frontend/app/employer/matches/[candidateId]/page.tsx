"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

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
      <p className="text-sm text-secondary" role="status">
        Loading your account…
      </p>
    );
  }

  if (!user) {
    return (
      <div>
        <p className="text-sm text-danger" role="alert">
          {isError
            ? "We could not verify your session. Sign in to continue."
            : "Sign in to view candidate profiles."}
        </p>
        <Link
          href="/login"
          className="mt-4 inline-flex min-h-control items-center text-sm font-medium text-primary underline-offset-2 hover:underline"
        >
          Go to login
        </Link>
      </div>
    );
  }

  if (user.role !== "employer") {
    return (
      <div>
        <p className="text-sm text-secondary" role="status">
          Candidate profiles are available only to employer accounts.
        </p>
        <Link
          href="/"
          className="mt-4 inline-flex min-h-control items-center text-sm font-medium text-primary underline-offset-2 hover:underline"
        >
          Back to workspace
        </Link>
      </div>
    );
  }

  if (!candidateId || !vacancyId) {
    return (
      <div>
        <p className="text-sm text-danger" role="alert">
          A candidate and vacancy are required to open this profile.
        </p>
        <Link
          href="/"
          className="mt-4 inline-flex min-h-control items-center text-sm font-medium text-primary underline-offset-2 hover:underline"
        >
          Back to employer workspace
        </Link>
      </div>
    );
  }

  return (
    <>
      <header className="flex flex-col gap-6 border-b border-border pb-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-primary">BeyondResume</p>
          <p className="mt-2 text-sm text-secondary">Employer · Candidate profile</p>
        </div>
        <button
          type="button"
          onClick={onSignOutClick}
          className="min-h-control shrink-0 rounded-button border border-border bg-surface px-6 text-sm font-medium text-ink"
        >
          Logout
        </button>
      </header>

      <div className="mt-8">
        <CandidateProfileView
          candidateId={candidateId}
          vacancyId={vacancyId}
          enabled
        />
      </div>
    </>
  );
}

export default function EmployerMatchDetailsPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16 lg:px-8">
      <Suspense
        fallback={
          <p className="text-sm text-secondary" role="status">
            Loading candidate profile…
          </p>
        }
      >
        <MatchDetailsContent />
      </Suspense>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { CandidateProfileSection } from "@/features/candidate-profile-section";
import { EmployerSection } from "@/features/employer-section";
import { EvidenceHubSection } from "@/features/evidence-hub/evidence-hub-section";
import { GitHubSection } from "@/features/github-section";
import { ResumeSection } from "@/features/resume-section";
import { RoadmapSection } from "@/features/roadmap-section";
import { SkillPassportSection } from "@/features/skill-passport-section";
import { useCurrentUser, useLogout } from "@/lib/auth/hooks";

export default function HomePage() {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();

  function onSignOutClick() {
    logout();
    router.push("/login");
  }

  if (isLoading) {
    return (
      <PageContainer>
        <div role="status" aria-label="Loading account" className="space-y-3">
          <SkeletonText className="h-4 w-28" />
          <SkeletonText className="h-8 w-64" />
          <SkeletonText className="h-4 w-48" />
        </div>
      </PageContainer>
    );
  }

  if (!user) {
    return (
      <PageContainer className="flex min-h-screen items-center">
        <section className="max-w-2xl" aria-labelledby="public-home-title">
          <p className="text-sm font-medium text-primary">BeyondResume</p>
          <h1 id="public-home-title" className="mt-4 text-4xl font-semibold text-ink">
            Show what you can do, beyond the resume.
          </h1>
          <p className="mt-6 text-lg leading-8 text-secondary">
            Build an evidence-based professional profile that helps employers understand your
            verified skills, experience, and potential.
          </p>

          {isError ? (
            <p className="mt-6 text-sm text-danger" role="alert">
              We could not verify your session. Sign in to continue.
            </p>
          ) : null}

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="inline-flex min-h-control items-center justify-center rounded-button border border-primary bg-primary px-6 text-sm font-medium text-white transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="inline-flex min-h-control items-center justify-center rounded-button border border-border bg-surface px-6 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Register
            </Link>
          </div>
        </section>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        breadcrumb={<span className="font-medium text-primary">BeyondResume</span>}
        title={user.role === "employer" ? "Employer workspace" : "Candidate workspace"}
        description={`Signed in as ${user.email} · ${user.role}`}
        actions={
          <Button type="button" variant="secondary" onClick={onSignOutClick}>
            Logout
          </Button>
        }
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {user.role === "employer" ? (
          <EmployerSection enabled />
        ) : (
          <>
            <CandidateDashboardSection enabled={user.role === "candidate"} />
            <CandidateProfileSection enabled={user.role === "candidate"} />
            <EvidenceHubSection enabled={user.role === "candidate"} />
            <ResumeSection enabled={user.role === "candidate"} />
            <GitHubSection enabled={user.role === "candidate"} />
            <SkillPassportSection enabled={user.role === "candidate"} />
            <RoadmapSection enabled={user.role === "candidate"} />
          </>
        )}
      </div>
    </PageContainer>
  );
}

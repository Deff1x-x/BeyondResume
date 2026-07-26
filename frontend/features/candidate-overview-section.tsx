"use client";

import Link from "next/link";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { primaryActionClass, secondaryActionClass } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { SkeletonCard } from "@/components/ui/skeleton";
import { CandidateVacanciesPreview } from "@/features/candidate-vacancies-section";
import { OnboardingChecklist } from "@/features/onboarding/checklist";
import { OnboardingGuidedNextStep } from "@/features/onboarding/guided-next-step";
import { OnboardingWelcomeCard } from "@/features/onboarding/welcome-card";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";
import { ApiClientError } from "@/lib/api/error";
import type { CandidateDashboardResponse } from "@/lib/api/types/dashboard";
import { useCandidateDashboardQuery } from "@/lib/dashboard/hooks";
import { useCurrentResumeQuery } from "@/lib/resume/hooks";

const secondaryLinkClass = secondaryActionClass;

function isResumeMissing(error: unknown): boolean {
  return error instanceof ApiClientError && error.code === "RESUME_NOT_FOUND";
}

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "Your overview could not be loaded. Please try again.";
}

type ResumeState = "available" | "missing" | "checking" | "processing" | "failed";

function EvidenceHealth({
  dashboard,
  resumeState
}: Readonly<{
  dashboard: CandidateDashboardResponse;
  resumeState: ResumeState;
}>) {
  const githubLabel = dashboard.github.connected
    ? `${dashboard.github.repositories} ${dashboard.github.repositories === 1 ? "repository" : "repositories"}`
    : "Not connected";
  const passportLabel = dashboard.passport.skills === 0
    ? "Not generated"
    : `${dashboard.passport.skills} confirmed skills`;

  const resume = resumeState === "available"
    ? { value: "Evidence added", status: "completed", statusLabel: "Complete" }
    : resumeState === "processing"
      ? { value: "Processing", status: "processing", statusLabel: "Processing" }
      : resumeState === "failed"
        ? { value: "Needs attention", status: "failed", statusLabel: "Needs attention" }
        : resumeState === "checking"
          ? { value: "Checking", status: "pending", statusLabel: "Checking" }
          : { value: "Not added", status: "not_started", statusLabel: "Not added" };
  const sources = [
    { label: "GitHub", value: githubLabel, status: dashboard.github.connected ? "completed" : "not_started", icon: "github" as const },
    { label: "Resume", ...resume, icon: "resume" as const },
    { label: "Skill Passport", value: passportLabel, status: dashboard.passport.skills > 0 ? "completed" : "not_started", icon: "passport" as const },
    { label: "Evidence", value: `${dashboard.evidence.count} ${dashboard.evidence.count === 1 ? "unit" : "units"}`, status: dashboard.evidence.count > 0 ? "completed" : "not_started", icon: "evidence" as const }
  ];

  return (
    <section aria-labelledby="evidence-health-title">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Evidence health</p>
          <h2 id="evidence-health-title" className="mt-1 text-xl font-semibold tracking-tight text-ink">Your connected evidence</h2>
        </div>
        <a href="#evidence-section" className="app-link text-sm">View evidence</a>
      </div>
      <div className="stagger-children grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {sources.map((source) => (
          <Card key={source.label} className="surface-lift bg-surface/90">
            <CardContent className="flex items-start gap-3 p-4">
              <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-card bg-accent/20 text-accent-muted">
                <Icon name={source.icon} className="h-[18px] w-[18px]" />
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink">{source.label}</p>
                <p className="mt-1 break-words text-sm text-secondary">{source.value}</p>
                <StatusBadge className="mt-2" status={source.status} label={"statusLabel" in source ? source.statusLabel : undefined} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}

function TopSkillsPreview({ dashboard }: Readonly<{ dashboard: CandidateDashboardResponse }>) {
  const skills = dashboard.passport.top_skills.slice(0, 5);

  return (
    <section aria-labelledby="top-skills-title">
      <Card>
        <CardContent className="p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Skill Passport</p>
              <h2 id="top-skills-title" className="mt-1 text-xl font-semibold tracking-tight text-ink">Top confirmed skills</h2>
              <p className="mt-2 text-sm leading-6 text-secondary">A compact preview of the strongest skills already supported by your evidence.</p>
            </div>
            <Link href="/skill-passport" className={secondaryLinkClass}>View full passport</Link>
          </div>

          {skills.length > 0 ? (
            <ul className="mt-5 flex flex-wrap gap-2" aria-label="Top confirmed skills">
              {skills.map((skill) => <li key={skill}><Badge variant="primary">{skill}</Badge></li>)}
            </ul>
          ) : (
            <EmptyState
              className="mt-5 bg-background py-6"
              icon={<Icon name="passport" className="h-7 w-7" />}
              title="You haven't generated your Skill Passport yet."
              description="Connect sources and open Skill Passport to confirm skills from your evidence."
              primaryAction={<Link href="/skill-passport" className={primaryActionClass}>Generate Skill Passport</Link>}
            />
          )}
        </CardContent>
      </Card>
    </section>
  );
}

function CompletedOnboardingBanner() {
  const { progress, restartTour, ready } = useCandidateOnboarding();
  if (!ready || !progress.isComplete) {
    return null;
  }

  return (
    <Card className="border-success/25 bg-success-soft/40">
      <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div>
          <p className="text-sm font-semibold text-ink">Getting started complete</p>
          <p className="mt-1 text-sm leading-6 text-secondary">
            You can keep improving your evidence anytime. Replay the short tour if you need a refresher.
          </p>
        </div>
        <button
          type="button"
          className={secondaryLinkClass}
          onClick={restartTour}
        >
          Restart tour
        </button>
      </CardContent>
    </Card>
  );
}

export function CandidateOverviewSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const dashboardQuery = useCandidateDashboardQuery(enabled);
  const resumeQuery = useCurrentResumeQuery(enabled);

  if (dashboardQuery.isLoading) {
    return <div className="grid gap-6" role="status" aria-label="Loading candidate overview"><SkeletonCard className="min-h-64" /><SkeletonCard className="min-h-52" /><SkeletonCard className="min-h-48" /></div>;
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return <EmptyState role="alert" title="Overview unavailable" description={errorMessage(dashboardQuery.error)} primaryAction={<button type="button" className={secondaryLinkClass} onClick={() => void dashboardQuery.refetch()}>Try again</button>} />;
  }

  const dashboard = dashboardQuery.data;
  const resumeState: ResumeState = resumeQuery.isLoading || (resumeQuery.isError && !isResumeMissing(resumeQuery.error))
    ? "checking"
    : resumeQuery.data?.evidence_id
      ? "available"
      : resumeQuery.data?.status === "failed"
        ? "failed"
        : resumeQuery.data
          ? "processing"
          : "missing";

  return (
    <div className="space-y-10">
      <div id="overview-section" className="scroll-mt-[var(--workspace-scroll-offset)] space-y-10">
        <OnboardingWelcomeCard />
        <OnboardingChecklist />
        <OnboardingGuidedNextStep />
        <CompletedOnboardingBanner />
        <EvidenceHealth dashboard={dashboard} resumeState={resumeState} />
      </div>

      <div id="skill-passport-section" className="scroll-mt-[var(--workspace-scroll-offset)]">
        <TopSkillsPreview dashboard={dashboard} />
      </div>

      <section
        id="opportunities-section"
        className="scroll-mt-[var(--workspace-scroll-offset)]"
        aria-labelledby="recommended-vacancies-title"
      >
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Opportunities</p>
            <h2 id="recommended-vacancies-title" className="mt-1 text-xl font-semibold tracking-tight text-ink">Recommended vacancies</h2>
            <p className="mt-1 text-sm leading-6 text-secondary">Existing vacancy matches, ordered by the current matching experience.</p>
          </div>
          <Link href="/vacancies" className="app-link text-sm">View all opportunities</Link>
        </div>
        <CandidateVacanciesPreview />
      </section>
    </div>
  );
}

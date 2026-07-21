"use client";

import Link from "next/link";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon, type IconName } from "@/components/ui/icon";
import { SkeletonCard } from "@/components/ui/skeleton";
import { CandidateVacanciesPreview } from "@/features/candidate-vacancies-section";
import { ApiClientError } from "@/lib/api/error";
import type { CandidateDashboardResponse } from "@/lib/api/types/dashboard";
import { useCandidateDashboardQuery } from "@/lib/dashboard/hooks";
import { useCurrentResumeQuery } from "@/lib/resume/hooks";

const primaryLinkClass =
  "inline-flex min-h-control items-center justify-center rounded-button border border-primary bg-gradient-to-b from-indigo-500 to-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px hover:from-indigo-400 hover:to-primary hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2";

const secondaryLinkClass =
  "inline-flex min-h-control items-center justify-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition hover:border-border-strong hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2";

function isResumeMissing(error: unknown): boolean {
  return error instanceof ApiClientError && error.code === "RESUME_NOT_FOUND";
}

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "Your overview could not be loaded. Please try again.";
}

type SetupItemProps = {
  label: string;
  description: string;
  complete: boolean | null;
  optional?: boolean;
  icon: IconName;
};

type ResumeState = "available" | "missing" | "checking" | "processing" | "failed";

function SetupItem({ label, description, complete, optional = false, icon }: Readonly<SetupItemProps>) {
  const status = complete === null ? "checking" : complete ? "completed" : "not_started";
  const labelText = complete === null ? "Checking" : complete ? "Complete" : optional ? "Optional" : "Not started";

  return (
    <li className="flex min-w-0 items-start gap-3 rounded-xl bg-background/70 p-3">
      <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <Icon name={icon} className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-ink">{label}</p>
          <StatusBadge status={status} label={labelText} />
        </div>
        <p className="mt-1 text-sm leading-5 text-secondary">{description}</p>
      </div>
    </li>
  );
}

type NextStep = {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
  action: string;
  icon: IconName;
};

function nextStepFor(dashboard: CandidateDashboardResponse): NextStep {
  if (!dashboard.github.connected) {
    return {
      eyebrow: "Recommended next step",
      title: "Connect a GitHub repository",
      description: "Bring verified project evidence into your Skill Passport.",
      href: "#github-section-title",
      action: "Connect GitHub",
      icon: "github"
    };
  }

  if (dashboard.passport.skills === 0) {
    return {
      eyebrow: "Recommended next step",
      title: "Review your Skill Passport",
      description: "Your connected sources can now be used to confirm the skills behind your work.",
      href: "/skill-passport",
      action: "Open Skill Passport",
      icon: "passport"
    };
  }

  return {
    eyebrow: "Recommended next step",
    title: "Explore matching vacancies",
    description: "See how your confirmed skills align with currently available opportunities.",
    href: "/vacancies",
    action: "Explore opportunities",
    icon: "dashboard"
  };
}

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
        <a href="#evidence-hub-section-title" className="app-link text-sm">View evidence</a>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {sources.map((source) => (
          <Card key={source.label} className="bg-surface/90">
            <CardContent className="flex items-start gap-3 p-4">
              <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
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
              title="No confirmed skills yet"
              description="Connect a repository or upload your resume to start building evidence for your skills."
              primaryAction={<a href="#github-section-title" className={secondaryLinkClass}>Connect GitHub</a>}
            />
          )}
        </CardContent>
      </Card>
    </section>
  );
}

function SetupProgress({
  dashboard,
  resumeState
}: Readonly<{
  dashboard: CandidateDashboardResponse;
  resumeState: ResumeState;
}>) {
  const items: SetupItemProps[] = [
    { label: "Connect GitHub", description: "Link a public repository for project evidence.", complete: dashboard.github.connected, icon: "github" },
    { label: "Add resume evidence", description: "Optional context for your stated experience.", complete: resumeState === "checking" || resumeState === "processing" ? null : resumeState === "available", optional: true, icon: "resume" },
    { label: "Build Skill Passport", description: "Confirm skills from your connected evidence.", complete: dashboard.passport.skills > 0, icon: "passport" }
  ];
  const requiredItems = items.filter((item) => !item.optional);
  const completed = requiredItems.filter((item) => item.complete === true).length;

  return (
    <section aria-labelledby="setup-progress-title">
      <Card className="border-primary/15 bg-gradient-to-br from-primary/10 via-surface to-cyan-50/60">
        <CardContent className="p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Setup progress</p>
              <h2 id="setup-progress-title" className="mt-1 text-xl font-semibold tracking-tight text-ink">Strengthen your evidence profile</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">Complete the available evidence sources at your own pace. Resume evidence remains optional.</p>
            </div>
            <div className="min-w-40 rounded-xl border border-primary/15 bg-surface/80 px-4 py-3">
              <p className="text-2xl font-semibold tabular-nums text-ink">{completed}/{requiredItems.length}</p>
              <p className="mt-1 text-xs font-medium text-secondary">core setup items complete</p>
            </div>
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-primary/10" role="progressbar" aria-label="Evidence setup progress" aria-valuemin={0} aria-valuemax={requiredItems.length} aria-valuenow={completed}>
            <div className="h-full rounded-full bg-primary transition-[width] duration-300 motion-reduce:transition-none" style={{ width: `${(completed / requiredItems.length) * 100}%` }} />
          </div>
          <ul className="mt-5 grid gap-3 lg:grid-cols-3">
            {items.map((item) => <SetupItem key={item.label} {...item} />)}
          </ul>
        </CardContent>
      </Card>
    </section>
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
  const nextStep = nextStepFor(dashboard);

  return (
    <div className="space-y-10">
      <SetupProgress dashboard={dashboard} resumeState={resumeState} />

      <section aria-labelledby="recommended-next-step-title">
        <Card className="overflow-hidden border-primary/20 bg-surface">
          <CardContent className="grid gap-6 p-6 sm:p-7 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
            <div className="flex min-w-0 gap-4">
              <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-sm shadow-primary/25"><Icon name={nextStep.icon} className="h-5 w-5" /></span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">{nextStep.eyebrow}</p>
                <h2 id="recommended-next-step-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">{nextStep.title}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">{nextStep.description}</p>
              </div>
            </div>
            {nextStep.href.startsWith("/") ? <Link href={nextStep.href} className={primaryLinkClass}>{nextStep.action}</Link> : <a href={nextStep.href} className={primaryLinkClass}>{nextStep.action}</a>}
          </CardContent>
        </Card>
      </section>

      <EvidenceHealth dashboard={dashboard} resumeState={resumeState} />

      <TopSkillsPreview dashboard={dashboard} />

      <section aria-labelledby="recommended-vacancies-title">
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

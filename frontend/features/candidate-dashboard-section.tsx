"use client";

import { ApiClientError } from "@/lib/api/error";
import type { CandidateDashboardResponse } from "@/lib/api/types/dashboard";
import { useCandidateDashboardQuery } from "@/lib/dashboard/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The dashboard could not be loaded. Please try again.";
}

type DashboardCardProps = {
  title: string;
  summary: string;
  detail?: string;
  href: string;
  actionLabel: string;
};

function DashboardCard({
  title,
  summary,
  detail,
  href,
  actionLabel
}: Readonly<DashboardCardProps>) {
  return (
    <article className="rounded-card border border-border bg-background p-4">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-2 text-2xl font-semibold text-ink">{summary}</p>
      {detail ? <p className="mt-2 text-sm leading-6 text-secondary">{detail}</p> : null}
      <a
        href={href}
        className="mt-4 inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
      >
        {actionLabel}
      </a>
    </article>
  );
}

function dashboardCards(data: CandidateDashboardResponse): DashboardCardProps[] {
  return [
    {
      title: "GitHub",
      summary: data.github.connected
        ? `${data.github.repositories} connected`
        : "Not connected",
      detail: data.github.connected
        ? "Repository linked for analysis and evidence."
        : "Connect a repository to start collecting evidence.",
      href: "#github-section-title",
      actionLabel: "Open GitHub"
    },
    {
      title: "Evidence",
      summary: String(data.evidence.count),
      detail:
        data.evidence.count === 1
          ? "1 evidence item collected from your sources."
          : `${data.evidence.count} evidence items collected from your sources.`,
      href: "#evidence-hub-section-title",
      actionLabel: "View evidence"
    },
    {
      title: "Skill Passport",
      summary: `${data.passport.skills} skills`,
      detail:
        data.passport.top_skills.length > 0
          ? `Top skills: ${data.passport.top_skills.join(", ")}`
          : "No confirmed skills yet.",
      href: "#skill-passport-section-title",
      actionLabel: "Open passport"
    },
    {
      title: "Roadmap",
      summary: `${data.roadmap.items} recommendations`,
      detail:
        data.roadmap.items > 0
          ? "Deterministic next steps based on your passport."
          : "Collect more evidence to unlock recommendations.",
      href: "#roadmap-section-title",
      actionLabel: "Open roadmap"
    }
  ];
}

export function CandidateDashboardSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const dashboardQuery = useCandidateDashboardQuery(enabled);

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
        aria-labelledby="dashboard-section-title"
      >
        <h2 id="dashboard-section-title" className="text-xl font-semibold text-ink">
          Dashboard
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          The candidate dashboard is available only to candidate accounts.
        </p>
      </section>
    );
  }

  return (
    <section
      className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
      aria-labelledby="dashboard-section-title"
    >
      <h2 id="dashboard-section-title" className="text-xl font-semibold text-ink">
        Dashboard
      </h2>
      <p className="mt-2 text-sm text-secondary">
        A summary of your GitHub, evidence, skill passport, and roadmap.
      </p>

      <div className="mt-6">
        {dashboardQuery.isLoading ? (
          <p className="text-sm text-secondary" role="status">
            Loading dashboard…
          </p>
        ) : null}

        {dashboardQuery.isError ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(dashboardQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void dashboardQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Try again
            </button>
          </div>
        ) : null}

        {dashboardQuery.data ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {dashboardCards(dashboardQuery.data).map((card) => (
              <DashboardCard key={card.title} {...card} />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

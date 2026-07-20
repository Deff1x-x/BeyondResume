"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonCard } from "@/components/ui/skeleton";
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
    <Card className="bg-background">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <p className="text-2xl font-semibold tabular-nums text-ink">{summary}</p>
        {detail ? <CardDescription>{detail}</CardDescription> : null}
      </CardHeader>
      <CardFooter className="border-t-0 pt-0">
        <a
          href={href}
          className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        >
          {actionLabel}
        </a>
      </CardFooter>
    </Card>
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
      href: "/skill-passport",
      actionLabel: "Open Skill Passport"
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
      <Card className="lg:col-span-2" aria-labelledby="dashboard-section-title">
        <CardContent className="p-6">
          <SectionHeader
            title="Dashboard"
            icon="dashboard"
            titleId="dashboard-section-title"
            description="The candidate dashboard is available only to candidate accounts."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="lg:col-span-2" aria-labelledby="dashboard-section-title">
      <CardContent className="space-y-6 p-6">
        <SectionHeader
          title="Dashboard"
          icon="dashboard"
          titleId="dashboard-section-title"
          description="A summary of your GitHub, evidence, skill passport, and roadmap."
        />

        <div aria-live="polite">
          {dashboardQuery.isLoading ? (
            <div
              className="grid gap-4 sm:grid-cols-2"
              role="status"
              aria-label="Loading dashboard"
            >
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : null}

          {dashboardQuery.isError ? (
            <EmptyState
              role="alert"
              title="Dashboard unavailable"
              description={errorMessage(dashboardQuery.error)}
              primaryAction={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void dashboardQuery.refetch()}
                >
                  Try again
                </Button>
              }
            />
          ) : null}

          {dashboardQuery.data ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {dashboardCards(dashboardQuery.data).map((card) => (
                <DashboardCard key={card.title} {...card} />
              ))}
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

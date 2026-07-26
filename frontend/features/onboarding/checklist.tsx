"use client";

import Link from "next/link";

import { AnimatedCounter } from "@/components/ui/animated-counter";
import { StatusBadge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";
import { cn } from "@/lib/cn";

export function OnboardingChecklist() {
  const { showChecklist, progress, collapseChecklist } = useCandidateOnboarding();

  if (!showChecklist) {
    return null;
  }

  return (
    <section aria-labelledby="getting-started-title">
      <Card className="border-primary/15 bg-primary/5">
        <CardContent className="p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Getting started</p>
              <h2 id="getting-started-title" className="mt-1 text-xl font-semibold tracking-tight text-ink">
                Your first steps
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
                Follow this checklist to build an evidence-based profile. GitHub is optional but recommended.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="min-w-40 rounded-card border border-primary/15 bg-surface/80 px-4 py-3">
                <p className="text-2xl font-semibold tabular-nums text-ink">
                  <AnimatedCounter value={progress.completedCount} />/{progress.totalCount}
                </p>
                <p className="mt-1 text-xs font-medium text-secondary">{progress.percentComplete}% complete</p>
              </div>
              <button
                type="button"
                className="rounded-control px-2 py-1 text-xs font-medium text-secondary hover:bg-surface hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                onClick={collapseChecklist}
              >
                Hide
              </button>
            </div>
          </div>

          <div
            className="mt-5 h-2 overflow-hidden rounded-full bg-primary/10"
            role="progressbar"
            aria-label="Getting started progress"
            aria-valuemin={0}
            aria-valuemax={progress.totalCount}
            aria-valuenow={progress.completedCount}
          >
            <div
              className="progress-fill h-full rounded-full bg-accent"
              style={{ width: `${progress.percentComplete}%` }}
            />
          </div>

          <ul className="mt-5 grid gap-3 lg:grid-cols-2">
            {progress.steps.map((step) => {
              const status = step.complete ? "completed" : step.optional ? "not_started" : "not_started";
              const labelText = step.complete ? "Complete" : step.optional ? "Optional" : "Not started";
              const content = (
                <>
                  <span
                    className={cn(
                      "mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-control",
                      step.complete ? "bg-success-soft text-success" : "bg-accent/20 text-accent-muted"
                    )}
                    aria-hidden="true"
                  >
                    <Icon name={step.complete ? "check-circle" : "dashboard"} className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-medium text-ink">{step.label}</p>
                      <StatusBadge status={status} label={labelText} />
                    </div>
                    <p className="mt-1 text-sm leading-5 text-secondary">{step.description}</p>
                  </div>
                </>
              );

              return (
                <li key={step.id}>
                  {step.complete ? (
                    <div className="surface-lift flex min-w-0 items-start gap-3 rounded-card bg-background/70 p-3">
                      {content}
                    </div>
                  ) : step.href.startsWith("/") && !step.href.includes("#") ? (
                    <Link
                      href={step.href}
                      className="surface-lift flex min-w-0 items-start gap-3 rounded-card bg-background/70 p-3 transition hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                    >
                      {content}
                    </Link>
                  ) : (
                    <a
                      href={step.href}
                      className="surface-lift flex min-w-0 items-start gap-3 rounded-card bg-background/70 p-3 transition hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                    >
                      {content}
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>
    </section>
  );
}

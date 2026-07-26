"use client";

import { Button, primaryActionClass, secondaryActionClass } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";

export function OnboardingWelcomeCard() {
  const { showWelcome, dismissWelcome, progress, restartTour, preferences } = useCandidateOnboarding();

  if (!showWelcome) {
    return null;
  }

  const tourAvailable = preferences.tourCompleted || preferences.tourSkipped;

  return (
    <Card className="border-accent/35 bg-surface shadow-card" aria-labelledby="onboarding-welcome-title">
      <CardContent className="grid gap-6 p-6 sm:p-7 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
        <div className="flex min-w-0 gap-4">
          <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-card bg-accent text-accent-foreground shadow-sm shadow-accent/25">
            <Icon name="dashboard" className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Welcome</p>
            <h2 id="onboarding-welcome-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">
              Welcome to BeyondResume
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
              We&apos;ll help you build an evidence-based profile and discover the best matching opportunities.
              Complete these steps to unlock your full profile.
            </p>
            <p className="mt-3 text-sm font-medium text-ink" aria-live="polite">
              {progress.completedCount} / {progress.totalCount} completed · {progress.percentComplete}%
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {tourAvailable ? (
            <Button type="button" variant="secondary" onClick={restartTour}>
              Restart tour
            </Button>
          ) : null}
          <button type="button" className={secondaryActionClass} onClick={dismissWelcome}>
            Dismiss
          </button>
          {progress.nextStep ? (
            <a href={progress.nextStep.href} className={primaryActionClass}>
              {progress.nextStep.label}
            </a>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

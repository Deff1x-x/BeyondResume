"use client";

import Link from "next/link";

import { primaryActionClass } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icon, type IconName } from "@/components/ui/icon";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";
import { celebrationCopy } from "@/lib/onboarding/progress";
import type { OnboardingStepId } from "@/lib/onboarding/types";

const stepIcons: Record<OnboardingStepId, IconName> = {
  profile: "profile",
  resume: "resume",
  github: "github",
  evidence: "evidence",
  "skill-passport": "passport",
  vacancies: "dashboard",
  "career-companion": "spark"
};

export function OnboardingGuidedNextStep() {
  const { ready, progress } = useCandidateOnboarding();

  if (!ready || progress.isComplete || !progress.nextStep) {
    return null;
  }

  const completed = [...progress.steps].reverse().find((step) => step.complete);
  const copy = completed
    ? celebrationCopy(completed.label, progress.nextStep)
    : {
        eyebrow: "Recommended next step",
        title: progress.nextStep.label,
        description: progress.nextStep.description
      };

  const href = progress.nextStep.href;
  const actionLabel = progress.nextStep.label;
  const icon = stepIcons[progress.nextStep.id];

  return (
    <section aria-labelledby="onboarding-next-step-title">
      <Card className="overflow-hidden border-accent/35 bg-surface shadow-card">
        <CardContent className="grid gap-6 p-6 sm:p-7 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div className="flex min-w-0 gap-4">
            <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-card bg-accent text-accent-foreground shadow-sm shadow-accent/25">
              <Icon name={icon} className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">{copy.eyebrow}</p>
              <h2 id="onboarding-next-step-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">
                {copy.title}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">{copy.description}</p>
            </div>
          </div>
          {href.startsWith("/") && !href.includes("#") ? (
            <Link href={href} className={primaryActionClass}>
              {actionLabel}
            </Link>
          ) : (
            <a href={href} className={primaryActionClass}>
              {actionLabel}
            </a>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

import {
  DEFAULT_ONBOARDING_PREFERENCES,
  ONBOARDING_STEPS,
  type OnboardingPreferences,
  type OnboardingProgress,
  type OnboardingSignals,
  type OnboardingStepStatus
} from "@/lib/onboarding/types";

function signalFor(
  id: OnboardingStepStatus["id"],
  signals: OnboardingSignals
): boolean {
  switch (id) {
    case "profile":
      return signals.hasProfile;
    case "resume":
      return signals.hasResume;
    case "github":
      return signals.hasGitHub;
    case "evidence":
      return signals.hasEvidence;
    case "skill-passport":
      return signals.hasSkillPassport;
    case "vacancies":
      return signals.hasExploredVacancies;
    case "career-companion":
      return signals.hasCareerPlan;
    default:
      return false;
  }
}

export function deriveOnboardingProgress(signals: OnboardingSignals): OnboardingProgress {
  const steps: OnboardingStepStatus[] = ONBOARDING_STEPS.map((step) => ({
    id: step.id,
    label: step.label,
    description: step.description,
    href: step.href,
    optional: Boolean(step.optional),
    navLabel: step.navLabel,
    complete: signalFor(step.id, signals)
  }));

  const completedCount = steps.filter((step) => step.complete).length;
  const totalCount = steps.length;
  const percentComplete = totalCount === 0 ? 0 : Math.round((completedCount / totalCount) * 100);
  const nextStep = steps.find((step) => !step.complete) ?? null;
  const requiredIncomplete = steps.filter((step) => !step.optional && !step.complete);
  const isComplete = requiredIncomplete.length === 0;

  const incompleteNavLabels = [
    ...new Set(
      steps
        .filter((step) => !step.complete && step.navLabel)
        .map((step) => step.navLabel as string)
    )
  ];

  return {
    steps,
    completedCount,
    totalCount,
    percentComplete,
    nextStep,
    isComplete,
    incompleteNavLabels
  };
}

export function celebrationCopy(completedStepLabel: string, next: OnboardingStepStatus | null): {
  eyebrow: string;
  title: string;
  description: string;
} {
  if (!next) {
    return {
      eyebrow: "You're set",
      title: "Your profile foundation is ready",
      description: "Keep adding evidence and revisit Career Companion as your goals change."
    };
  }

  return {
    eyebrow: "Great progress",
    title: `${completedStepLabel} is done`,
    description: `Next, ${next.label.charAt(0).toLowerCase()}${next.label.slice(1)}.`
  };
}

export function mergePreferences(
  stored: Partial<OnboardingPreferences> | null | undefined
): OnboardingPreferences {
  return {
    ...DEFAULT_ONBOARDING_PREFERENCES,
    ...(stored ?? {})
  };
}

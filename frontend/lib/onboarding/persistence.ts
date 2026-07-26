import {
  DEFAULT_ONBOARDING_PREFERENCES,
  type OnboardingPreferences
} from "@/lib/onboarding/types";
import { mergePreferences } from "@/lib/onboarding/progress";

const STORAGE_PREFIX = "beyondresume_onboarding_v1:";

function storageKey(userId: string): string {
  return `${STORAGE_PREFIX}${userId}`;
}

export function readOnboardingPreferences(userId: string): OnboardingPreferences {
  if (typeof window === "undefined") {
    return { ...DEFAULT_ONBOARDING_PREFERENCES };
  }

  try {
    const raw = window.localStorage.getItem(storageKey(userId));
    if (!raw) {
      return { ...DEFAULT_ONBOARDING_PREFERENCES };
    }
    return mergePreferences(JSON.parse(raw) as Partial<OnboardingPreferences>);
  } catch {
    return { ...DEFAULT_ONBOARDING_PREFERENCES };
  }
}

export function writeOnboardingPreferences(
  userId: string,
  patch: Partial<OnboardingPreferences>
): OnboardingPreferences {
  const next = mergePreferences({
    ...readOnboardingPreferences(userId),
    ...patch
  });

  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(storageKey(userId), JSON.stringify(next));
    } catch {
      // Ignore quota / private-mode failures; in-memory state still works for the session.
    }
  }

  return next;
}

export function shouldOfferTour(prefs: OnboardingPreferences): boolean {
  return !prefs.tourCompleted && !prefs.tourSkipped;
}

export function shouldShowWelcome(prefs: OnboardingPreferences, onboardingComplete: boolean): boolean {
  return !prefs.welcomeDismissed && !onboardingComplete;
}

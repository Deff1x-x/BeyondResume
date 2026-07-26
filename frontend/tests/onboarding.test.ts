import { afterEach, describe, expect, it, vi } from "vitest";

import {
  readOnboardingPreferences,
  shouldOfferTour,
  shouldShowWelcome,
  writeOnboardingPreferences
} from "@/lib/onboarding/persistence";
import { celebrationCopy, deriveOnboardingProgress } from "@/lib/onboarding/progress";
import { DEFAULT_ONBOARDING_PREFERENCES } from "@/lib/onboarding/types";

afterEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe("deriveOnboardingProgress", () => {
  it("starts empty for a first-login candidate", () => {
    const progress = deriveOnboardingProgress({
      hasProfile: false,
      hasResume: false,
      hasGitHub: false,
      hasEvidence: false,
      hasSkillPassport: false,
      hasExploredVacancies: false,
      hasCareerPlan: false
    });

    expect(progress.completedCount).toBe(0);
    expect(progress.totalCount).toBe(7);
    expect(progress.percentComplete).toBe(0);
    expect(progress.isComplete).toBe(false);
    expect(progress.nextStep?.id).toBe("profile");
    expect(progress.incompleteNavLabels).toContain("Profile");
    expect(progress.incompleteNavLabels).toContain("GitHub");
  });

  it("updates progress as signals complete and keeps GitHub optional", () => {
    const progress = deriveOnboardingProgress({
      hasProfile: true,
      hasResume: true,
      hasGitHub: false,
      hasEvidence: true,
      hasSkillPassport: true,
      hasExploredVacancies: true,
      hasCareerPlan: false
    });

    expect(progress.completedCount).toBe(5);
    expect(progress.percentComplete).toBe(71);
    expect(progress.nextStep?.id).toBe("github");
    expect(progress.steps.find((step) => step.id === "github")?.optional).toBe(true);
    expect(progress.isComplete).toBe(false);
  });

  it("marks onboarding complete when all required steps are done", () => {
    const progress = deriveOnboardingProgress({
      hasProfile: true,
      hasResume: true,
      hasGitHub: true,
      hasEvidence: true,
      hasSkillPassport: true,
      hasExploredVacancies: true,
      hasCareerPlan: true
    });

    expect(progress.completedCount).toBe(7);
    expect(progress.percentComplete).toBe(100);
    expect(progress.isComplete).toBe(true);
    expect(progress.nextStep).toBeNull();
  });

  it("suggests the next logical action after a completed step", () => {
    const progress = deriveOnboardingProgress({
      hasProfile: true,
      hasResume: true,
      hasGitHub: false,
      hasEvidence: false,
      hasSkillPassport: false,
      hasExploredVacancies: false,
      hasCareerPlan: false
    });
    const copy = celebrationCopy("Upload your resume", progress.nextStep);
    expect(copy.title).toContain("Upload your resume");
    expect(copy.description.toLowerCase()).toContain("connect github");
  });
});

describe("onboarding persistence", () => {
  it("persists welcome dismiss and tour skip for a user", () => {
    const userId = "user-1";
    expect(readOnboardingPreferences(userId)).toEqual(DEFAULT_ONBOARDING_PREFERENCES);

    writeOnboardingPreferences(userId, { welcomeDismissed: true, tourSkipped: true });
    const prefs = readOnboardingPreferences(userId);
    expect(prefs.welcomeDismissed).toBe(true);
    expect(prefs.tourSkipped).toBe(true);
    expect(shouldOfferTour(prefs)).toBe(false);
    expect(shouldShowWelcome(prefs, false)).toBe(false);
  });

  it("hides welcome when onboarding is complete even if not dismissed", () => {
    expect(shouldShowWelcome(DEFAULT_ONBOARDING_PREFERENCES, true)).toBe(false);
  });

  it("allows restarting the tour after completion", () => {
    const userId = "user-2";
    writeOnboardingPreferences(userId, { tourCompleted: true, welcomeDismissed: true });
    const restarted = writeOnboardingPreferences(userId, {
      tourCompleted: false,
      tourSkipped: false,
      welcomeDismissed: false,
      checklistCollapsed: false
    });
    expect(shouldOfferTour(restarted)).toBe(true);
    expect(shouldShowWelcome(restarted, false)).toBe(true);
  });
});

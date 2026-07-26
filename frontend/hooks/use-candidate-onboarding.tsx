"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

import { ApiClientError } from "@/lib/api/error";
import { useCurrentUser } from "@/lib/auth/hooks";
import { useCandidateProfileQuery } from "@/lib/candidate/hooks";
import { useCandidateVacanciesQuery } from "@/lib/candidate-vacancies/hooks";
import { useCareerCompanionQuery } from "@/lib/career-companion/hooks";
import { useCandidateDashboardQuery } from "@/lib/dashboard/hooks";
import {
  readOnboardingPreferences,
  shouldOfferTour,
  shouldShowWelcome,
  writeOnboardingPreferences
} from "@/lib/onboarding/persistence";
import { deriveOnboardingProgress } from "@/lib/onboarding/progress";
import {
  DEFAULT_ONBOARDING_PREFERENCES,
  type OnboardingPreferences,
  type OnboardingProgress
} from "@/lib/onboarding/types";
import { useCurrentResumeQuery } from "@/lib/resume/hooks";

type OnboardingContextValue = {
  enabled: boolean;
  ready: boolean;
  preferences: OnboardingPreferences;
  progress: OnboardingProgress;
  showWelcome: boolean;
  showTour: boolean;
  showChecklist: boolean;
  incompleteNavLabels: Set<string>;
  dismissWelcome: () => void;
  collapseChecklist: () => void;
  completeTour: () => void;
  skipTour: () => void;
  restartTour: () => void;
  markVacanciesExplored: () => void;
};

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

function isResumeAvailable(error: unknown, data: { evidence_id?: string | null } | null | undefined): boolean {
  if (data?.evidence_id) {
    return true;
  }
  if (error instanceof ApiClientError && error.code === "RESUME_NOT_FOUND") {
    return false;
  }
  return Boolean(data);
}

export function CandidateOnboardingProvider({
  enabled,
  children
}: Readonly<{ enabled: boolean; children: ReactNode }>) {
  const { data: user } = useCurrentUser();
  const userId = user?.id ?? null;

  const profileQuery = useCandidateProfileQuery(enabled && Boolean(userId));
  const dashboardQuery = useCandidateDashboardQuery(enabled && Boolean(userId));
  const resumeQuery = useCurrentResumeQuery(enabled && Boolean(userId));
  const vacanciesQuery = useCandidateVacanciesQuery(enabled && Boolean(userId));
  const companionQuery = useCareerCompanionQuery(enabled && Boolean(userId));

  const [preferences, setPreferences] = useState<OnboardingPreferences>(DEFAULT_ONBOARDING_PREFERENCES);
  const [prefsReady, setPrefsReady] = useState(false);

  useEffect(() => {
    if (!userId) {
      setPreferences(DEFAULT_ONBOARDING_PREFERENCES);
      setPrefsReady(false);
      return;
    }
    setPreferences(readOnboardingPreferences(userId));
    setPrefsReady(true);
  }, [userId]);

  const patchPreferences = useCallback(
    (patch: Partial<OnboardingPreferences>) => {
      if (!userId) {
        setPreferences((prev) => ({ ...prev, ...patch }));
        return;
      }
      const next = writeOnboardingPreferences(userId, patch);
      setPreferences(next);
    },
    [userId]
  );

  const hasApplication = Boolean(
    vacanciesQuery.data?.some((vacancy) => vacancy.application != null)
  );

  const progress = useMemo(() => {
    const dashboard = dashboardQuery.data;
    const profile = profileQuery.data;
    const companionMissing =
      companionQuery.isError &&
      companionQuery.error instanceof ApiClientError &&
      companionQuery.error.status === 404;

    return deriveOnboardingProgress({
      hasProfile: Boolean(profile?.display_name?.trim()),
      hasResume: isResumeAvailable(resumeQuery.error, resumeQuery.data),
      hasGitHub: Boolean(dashboard?.github.connected),
      hasEvidence: (dashboard?.evidence.count ?? 0) > 0,
      hasSkillPassport: (dashboard?.passport.skills ?? 0) > 0,
      hasExploredVacancies: preferences.exploredVacancies || hasApplication,
      hasCareerPlan: Boolean(companionQuery.data) && !companionMissing
    });
  }, [
    companionQuery.data,
    companionQuery.error,
    companionQuery.isError,
    dashboardQuery.data,
    hasApplication,
    preferences.exploredVacancies,
    profileQuery.data,
    resumeQuery.data,
    resumeQuery.error
  ]);

  const ready =
    prefsReady &&
    !profileQuery.isLoading &&
    !dashboardQuery.isLoading &&
    !resumeQuery.isLoading;

  const value = useMemo<OnboardingContextValue>(() => {
    const showWelcome = enabled && ready && shouldShowWelcome(preferences, progress.isComplete);
    const showTour = enabled && ready && shouldOfferTour(preferences);
    const showChecklist = enabled && ready && !progress.isComplete && !preferences.checklistCollapsed;

    return {
      enabled,
      ready,
      preferences,
      progress,
      showWelcome,
      showTour,
      showChecklist,
      incompleteNavLabels: new Set(progress.incompleteNavLabels),
      dismissWelcome: () => patchPreferences({ welcomeDismissed: true }),
      collapseChecklist: () => patchPreferences({ checklistCollapsed: true }),
      completeTour: () => patchPreferences({ tourCompleted: true, tourSkipped: false }),
      skipTour: () => patchPreferences({ tourSkipped: true, tourCompleted: false }),
      restartTour: () =>
        patchPreferences({
          tourCompleted: false,
          tourSkipped: false,
          welcomeDismissed: false,
          checklistCollapsed: false
        }),
      markVacanciesExplored: () => patchPreferences({ exploredVacancies: true })
    };
  }, [enabled, patchPreferences, preferences, progress, ready]);

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useCandidateOnboarding(): OnboardingContextValue {
  const value = useContext(OnboardingContext);
  if (!value) {
    return {
      enabled: false,
      ready: true,
      preferences: DEFAULT_ONBOARDING_PREFERENCES,
      progress: deriveOnboardingProgress({
        hasProfile: true,
        hasResume: true,
        hasGitHub: true,
        hasEvidence: true,
        hasSkillPassport: true,
        hasExploredVacancies: true,
        hasCareerPlan: true
      }),
      showWelcome: false,
      showTour: false,
      showChecklist: false,
      incompleteNavLabels: new Set(),
      dismissWelcome: () => undefined,
      collapseChecklist: () => undefined,
      completeTour: () => undefined,
      skipTour: () => undefined,
      restartTour: () => undefined,
      markVacanciesExplored: () => undefined
    };
  }
  return value;
}

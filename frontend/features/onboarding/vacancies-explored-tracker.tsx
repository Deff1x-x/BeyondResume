"use client";

import { useEffect } from "react";

import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";

/** Marks the vacancies onboarding step complete when the opportunities page is opened. */
export function VacanciesExploredTracker() {
  const { markVacanciesExplored, enabled } = useCandidateOnboarding();

  useEffect(() => {
    if (!enabled) {
      return;
    }
    markVacanciesExplored();
  }, [enabled, markVacanciesExplored]);

  return null;
}

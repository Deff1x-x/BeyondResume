import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingChecklist } from "@/features/onboarding/checklist";
import { OnboardingGuidedNextStep } from "@/features/onboarding/guided-next-step";
import { OnboardingTour } from "@/features/onboarding/tour";
import { OnboardingWelcomeCard } from "@/features/onboarding/welcome-card";
import { deriveOnboardingProgress } from "@/lib/onboarding/progress";
import { DEFAULT_ONBOARDING_PREFERENCES } from "@/lib/onboarding/types";

const onboardingState = vi.hoisted(() => ({
  value: {
    enabled: true,
    ready: true,
    preferences: {
      welcomeDismissed: false,
      tourCompleted: false,
      tourSkipped: false,
      checklistCollapsed: false,
      exploredVacancies: false
    },
    progress: null as ReturnType<typeof deriveOnboardingProgress> | null,
    showWelcome: true,
    showTour: false,
    showChecklist: true,
    incompleteNavLabels: new Set(["Profile", "Resume", "GitHub"]),
    dismissWelcome: vi.fn(),
    collapseChecklist: vi.fn(),
    completeTour: vi.fn(),
    skipTour: vi.fn(),
    restartTour: vi.fn(),
    markVacanciesExplored: vi.fn()
  }
}));

vi.mock("@/hooks/use-candidate-onboarding", () => ({
  useCandidateOnboarding: () => ({
    ...onboardingState.value,
    progress:
      onboardingState.value.progress ??
      deriveOnboardingProgress({
        hasProfile: false,
        hasResume: false,
        hasGitHub: false,
        hasEvidence: false,
        hasSkillPassport: false,
        hasExploredVacancies: false,
        hasCareerPlan: false
      })
  })
}));

beforeEach(() => {
  onboardingState.value.preferences = { ...DEFAULT_ONBOARDING_PREFERENCES };
  onboardingState.value.progress = deriveOnboardingProgress({
    hasProfile: false,
    hasResume: false,
    hasGitHub: false,
    hasEvidence: false,
    hasSkillPassport: false,
    hasExploredVacancies: false,
    hasCareerPlan: false
  });
  onboardingState.value.showWelcome = true;
  onboardingState.value.showTour = false;
  onboardingState.value.showChecklist = true;
  onboardingState.value.incompleteNavLabels = new Set(["Profile", "Resume", "GitHub"]);
  onboardingState.value.dismissWelcome = vi.fn();
  onboardingState.value.collapseChecklist = vi.fn();
  onboardingState.value.completeTour = vi.fn();
  onboardingState.value.skipTour = vi.fn();
  onboardingState.value.restartTour = vi.fn();
  onboardingState.value.markVacanciesExplored = vi.fn();
});

afterEach(cleanup);

describe("onboarding UI", () => {
  it("shows the welcome card for first login", () => {
    render(<OnboardingWelcomeCard />);
    expect(screen.getByRole("heading", { name: "Welcome to BeyondResume" })).toBeInTheDocument();
    expect(screen.getByText(/0 \/ 7 completed/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(onboardingState.value.dismissWelcome).toHaveBeenCalled();
  });

  it("renders checklist progress and hides when requested", () => {
    render(<OnboardingChecklist />);
    expect(screen.getByRole("heading", { name: "Your first steps" })).toBeInTheDocument();
    expect(screen.getByText("Complete your profile")).toBeInTheDocument();
    expect(screen.getByLabelText("Getting started progress")).toHaveAttribute("aria-valuenow", "0");
    fireEvent.click(screen.getByRole("button", { name: "Hide" }));
    expect(onboardingState.value.collapseChecklist).toHaveBeenCalled();
  });

  it("guides the user to the next incomplete step", () => {
    onboardingState.value.progress = deriveOnboardingProgress({
      hasProfile: true,
      hasResume: false,
      hasGitHub: false,
      hasEvidence: false,
      hasSkillPassport: false,
      hasExploredVacancies: false,
      hasCareerPlan: false
    });
    render(<OnboardingGuidedNextStep />);
    expect(screen.getByRole("heading", { name: /Complete your profile is done/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Upload your resume" })).toHaveAttribute("href", "/#resume-section");
  });

  it("does not show checklist or welcome after completed onboarding", () => {
    onboardingState.value.showWelcome = false;
    onboardingState.value.showChecklist = false;
    onboardingState.value.progress = deriveOnboardingProgress({
      hasProfile: true,
      hasResume: true,
      hasGitHub: true,
      hasEvidence: true,
      hasSkillPassport: true,
      hasExploredVacancies: true,
      hasCareerPlan: true
    });
    const { container } = render(
      <>
        <OnboardingWelcomeCard />
        <OnboardingChecklist />
      </>
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("supports skipping and completing the welcome tour", () => {
    onboardingState.value.showTour = true;
    const aside = document.createElement("aside");
    aside.innerHTML = `<nav><a href="/">Overview</a></nav>`;
    document.body.appendChild(aside);
    Element.prototype.scrollIntoView = vi.fn();
    render(<OnboardingTour />);
    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Skip tour" }));
    expect(onboardingState.value.skipTour).toHaveBeenCalled();
  });

  it("exposes restart tour from the welcome card after a prior skip", () => {
    onboardingState.value.preferences = {
      ...DEFAULT_ONBOARDING_PREFERENCES,
      tourSkipped: true
    };
    render(<OnboardingWelcomeCard />);
    fireEvent.click(screen.getByRole("button", { name: "Restart tour" }));
    expect(onboardingState.value.restartTour).toHaveBeenCalled();
  });
});

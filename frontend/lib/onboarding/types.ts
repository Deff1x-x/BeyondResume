export type OnboardingStepId =
  | "profile"
  | "resume"
  | "github"
  | "evidence"
  | "skill-passport"
  | "vacancies"
  | "career-companion";

export type OnboardingStep = {
  id: OnboardingStepId;
  label: string;
  description: string;
  href: string;
  optional?: boolean;
  /** Sidebar label that should show a Getting Started badge when incomplete. */
  navLabel?: string;
};

export type OnboardingSignals = {
  hasProfile: boolean;
  hasResume: boolean;
  hasGitHub: boolean;
  hasEvidence: boolean;
  hasSkillPassport: boolean;
  hasExploredVacancies: boolean;
  hasCareerPlan: boolean;
};

export type OnboardingStepStatus = {
  id: OnboardingStepId;
  label: string;
  description: string;
  href: string;
  optional: boolean;
  complete: boolean;
  navLabel?: string;
};

export type OnboardingProgress = {
  steps: OnboardingStepStatus[];
  completedCount: number;
  totalCount: number;
  percentComplete: number;
  nextStep: OnboardingStepStatus | null;
  isComplete: boolean;
  incompleteNavLabels: string[];
};

export type OnboardingPreferences = {
  welcomeDismissed: boolean;
  tourCompleted: boolean;
  tourSkipped: boolean;
  checklistCollapsed: boolean;
  exploredVacancies: boolean;
};

export const DEFAULT_ONBOARDING_PREFERENCES: OnboardingPreferences = {
  welcomeDismissed: false,
  tourCompleted: false,
  tourSkipped: false,
  checklistCollapsed: false,
  exploredVacancies: false
};

export const ONBOARDING_STEPS: readonly OnboardingStep[] = [
  {
    id: "profile",
    label: "Complete your profile",
    description: "Add your name so employers and matches can recognize you.",
    href: "/profile",
    navLabel: "Profile"
  },
  {
    id: "resume",
    label: "Upload your resume",
    description: "Use your resume as stated experience alongside verified evidence.",
    href: "/#resume-section",
    navLabel: "Resume"
  },
  {
    id: "github",
    label: "Connect GitHub",
    description: "Link a public repository to collect project evidence automatically.",
    href: "/#github-section",
    optional: true,
    navLabel: "GitHub"
  },
  {
    id: "evidence",
    label: "Add evidence",
    description: "Confirmations from connected sources power your Skill Passport.",
    href: "/#evidence-section",
    navLabel: "Evidence"
  },
  {
    id: "skill-passport",
    label: "Generate your Skill Passport",
    description: "Turn verified evidence into a clear skills profile.",
    href: "/skill-passport",
    navLabel: "Skill Passport"
  },
  {
    id: "vacancies",
    label: "Explore recommended vacancies",
    description: "See how your confirmed skills align with open roles.",
    href: "/vacancies",
    navLabel: "Opportunities"
  },
  {
    id: "career-companion",
    label: "Generate your first Career Companion plan",
    description: "Get an evidence-guided plan for what to learn next.",
    href: "/#career-companion-section",
    navLabel: "Career Companion"
  }
] as const;

export const ONBOARDING_TOUR_STEPS = [
  {
    id: "overview",
    target: "overview",
    title: "Overview",
    body: "Start here to see your progress and the next recommended action.",
    href: "/"
  },
  {
    id: "skill-passport",
    target: "Skill Passport",
    title: "Skill Passport",
    body: "Your confirmed skills appear here once evidence is connected.",
    href: "/skill-passport"
  },
  {
    id: "evidence",
    target: "Evidence",
    title: "Evidence",
    body: "Evidence is the proof behind every skill in your profile.",
    href: "/#evidence-section"
  },
  {
    id: "opportunities",
    target: "Opportunities",
    title: "Opportunities",
    body: "Matching vacancies update as your Skill Passport grows.",
    href: "/vacancies"
  },
  {
    id: "career-companion",
    target: "Career Companion",
    title: "Career Companion",
    body: "Generate a personalized growth plan grounded in your evidence.",
    href: "/#career-companion-section"
  }
] as const;

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateOverviewSection } from "@/features/candidate-overview-section";
import { deriveOnboardingProgress } from "@/lib/onboarding/progress";
import { DEFAULT_ONBOARDING_PREFERENCES } from "@/lib/onboarding/types";

const dashboardQuery = vi.fn();
const resumeQuery = vi.fn();
const vacanciesQuery = vi.fn();

vi.mock("@/lib/dashboard/hooks", () => ({
  useCandidateDashboardQuery: () => dashboardQuery()
}));

vi.mock("@/lib/resume/hooks", () => ({
  useCurrentResumeQuery: () => resumeQuery()
}));

vi.mock("@/lib/candidate-vacancies/hooks", () => ({
  useCandidateVacanciesQuery: () => vacanciesQuery(),
  useApplyToVacancy: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null
  }),
  useWithdrawApplication: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null
  })
}));

vi.mock("@/hooks/use-candidate-onboarding", () => ({
  useCandidateOnboarding: () => ({
    enabled: true,
    ready: true,
    preferences: DEFAULT_ONBOARDING_PREFERENCES,
    progress: deriveOnboardingProgress({
      hasProfile: false,
      hasResume: false,
      hasGitHub: false,
      hasEvidence: false,
      hasSkillPassport: false,
      hasExploredVacancies: false,
      hasCareerPlan: false
    }),
    showWelcome: true,
    showTour: false,
    showChecklist: true,
    incompleteNavLabels: new Set(["Profile"]),
    dismissWelcome: vi.fn(),
    collapseChecklist: vi.fn(),
    completeTour: vi.fn(),
    skipTour: vi.fn(),
    restartTour: vi.fn(),
    markVacanciesExplored: vi.fn()
  })
}));

function readyOverview({
  connected = false,
  skills = 0,
  topSkills = [],
  resume = null
}: {
  connected?: boolean;
  skills?: number;
  topSkills?: string[];
  resume?: object | null;
} = {}) {
  dashboardQuery.mockReturnValue({
    data: {
      github: { connected, repositories: connected ? 1 : 0 },
      evidence: { count: connected ? 3 : 0 },
      passport: { skills, top_skills: topSkills },
      roadmap: { items: 0 }
    },
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn()
  });
  resumeQuery.mockReturnValue({ data: resume, isLoading: false, isError: false, error: null });
  vacanciesQuery.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CandidateOverviewSection", () => {
  it("shows first-login welcome guidance and getting started checklist", () => {
    readyOverview();
    render(<CandidateOverviewSection enabled />);

    expect(screen.getByRole("heading", { name: "Welcome to BeyondResume" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Your first steps" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Complete your profile" })).toBeInTheDocument();
    expect(screen.getByText(/GitHub is optional but recommended/i)).toBeInTheDocument();
  });

  it("uses existing passport data for a compact top-skills preview and vacancy data for the existing preview order", () => {
    readyOverview({
      connected: true,
      skills: 6,
      topSkills: ["Python", "React", "TypeScript", "Docker", "FastAPI", "Redis"],
      resume: { id: "resume-1", status: "parsed", evidence_id: "evidence-1" }
    });
    vacanciesQuery.mockReturnValue({
      data: [
        {
          id: "vacancy-1",
          company_name: "Acme",
          title: "Platform Engineer",
          description: null,
          created_at: "2026-07-20T10:00:00Z",
          required_skills: [],
          preferred_skills: [],
          match: {
            score: 80,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          },
          application: null
        },
        {
          id: "vacancy-2",
          company_name: "Acme",
          title: "Frontend Engineer",
          description: null,
          created_at: "2026-07-20T10:00:00Z",
          required_skills: [],
          preferred_skills: [],
          match: {
            score: 70,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          },
          application: {
            id: "app-2",
            vacancy_id: "vacancy-2",
            candidate_id: "candidate-1",
            status: "applied",
            created_at: "2026-07-25T10:00:00Z",
            updated_at: "2026-07-25T10:00:00Z"
          }
        },
        {
          id: "vacancy-3",
          company_name: "Acme",
          title: "Backend Engineer",
          description: null,
          created_at: "2026-07-20T10:00:00Z",
          required_skills: [],
          preferred_skills: [],
          match: {
            score: 60,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          },
          application: null
        },
        {
          id: "vacancy-4",
          company_name: "Acme",
          title: "Data Engineer",
          description: null,
          created_at: "2026-07-20T10:00:00Z",
          required_skills: [],
          preferred_skills: [],
          match: {
            score: 50,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          },
          application: null
        }
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    });

    render(<CandidateOverviewSection enabled />);

    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.queryByText("Redis")).not.toBeInTheDocument();
    expect(screen.getByText("Platform Engineer")).toBeInTheDocument();
    expect(screen.getByText("Backend Engineer")).toBeInTheDocument();
    expect(screen.queryByText("Data Engineer")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View full passport" })).toHaveAttribute("href", "/skill-passport");

    expect(screen.getAllByRole("button", { name: /Apply now/i }).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Applied")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Withdraw/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /View details/i }).length).toBe(3);
  });

  it("does not fabricate recent activity when the available dashboard data has none", () => {
    readyOverview({ connected: true, skills: 1, topSkills: ["Python"] });
    render(<CandidateOverviewSection enabled />);

    expect(screen.queryByRole("heading", { name: "Recent activity" })).not.toBeInTheDocument();
  });
});

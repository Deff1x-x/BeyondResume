import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateOverviewSection } from "@/features/candidate-overview-section";

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
  useCandidateVacanciesQuery: () => vacanciesQuery()
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
  it("uses the existing GitHub connection condition for the only primary next step", () => {
    readyOverview();
    render(<CandidateOverviewSection enabled />);

    expect(screen.getByRole("heading", { name: "Connect a GitHub repository" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Connect GitHub" })[0]).toHaveAttribute("href", "#github-section-title");
    expect(screen.getByText(/Resume evidence remains optional/)).toBeInTheDocument();
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
        { id: "vacancy-1", company_name: "Acme", title: "Platform Engineer", description: null, required_skills: [], preferred_skills: [], match: { score: 80, required: { missing: [] }, preferred: { missing: [] } } },
        { id: "vacancy-2", company_name: "Acme", title: "Frontend Engineer", description: null, required_skills: [], preferred_skills: [], match: { score: 70, required: { missing: [] }, preferred: { missing: [] } } },
        { id: "vacancy-3", company_name: "Acme", title: "Backend Engineer", description: null, required_skills: [], preferred_skills: [], match: { score: 60, required: { missing: [] }, preferred: { missing: [] } } },
        { id: "vacancy-4", company_name: "Acme", title: "Data Engineer", description: null, required_skills: [], preferred_skills: [], match: { score: 50, required: { missing: [] }, preferred: { missing: [] } } }
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    });

    render(<CandidateOverviewSection enabled />);

    expect(screen.getByRole("heading", { name: "Explore matching vacancies" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Explore opportunities" })).toHaveAttribute("href", "/vacancies");
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.queryByText("Redis")).not.toBeInTheDocument();
    expect(screen.getByText("Platform Engineer")).toBeInTheDocument();
    expect(screen.getByText("Backend Engineer")).toBeInTheDocument();
    expect(screen.queryByText("Data Engineer")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View full passport" })).toHaveAttribute("href", "/skill-passport");
  });

  it("does not fabricate recent activity when the available dashboard data has none", () => {
    readyOverview({ connected: true, skills: 1, topSkills: ["Python"] });
    render(<CandidateOverviewSection enabled />);

    expect(screen.queryByRole("heading", { name: "Recent activity" })).not.toBeInTheDocument();
  });
});

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import type { SkillPassportResponse } from "@/lib/api/types/skill-passport";

const passportQuery = vi.fn();
const dashboardQuery = vi.fn();
const matchDetailsQuery = vi.fn();
const matchExplanationQuery = vi.fn();
const hiringIntelligenceQuery = vi.fn();

vi.mock("@/lib/skill-passport/hooks", () => ({
  useSkillPassportQuery: () => passportQuery()
}));

vi.mock("@/lib/dashboard/hooks", () => ({
  useCandidateDashboardQuery: () => dashboardQuery()
}));

vi.mock("@/lib/employer/hooks", () => ({
  useAddVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerCompany: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerVacancy: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useDeleteVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useEmployerCompanyQuery: () => ({ data: null, isLoading: false, isError: false }),
  useEmployerSkillsQuery: () => ({ data: [], isLoading: false, isError: false }),
  useEmployerVacanciesQuery: () => ({ data: [], isLoading: false, isError: false }),
  useEmployerVacancyQuery: () => ({ isLoading: false, isError: false, data: null }),
  useMatchDetailsQuery: () => matchDetailsQuery(),
  useMatchExplanationQuery: () => matchExplanationQuery(),
  useVacancyMatchesQuery: () => ({ data: { matches: [] }, isLoading: false, isError: false }),
  useVacancyRequirementsQuery: () => ({ data: [], isLoading: false, isError: false }),
  vacancyMatchesQueryKey: (vacancyId: string) => ["matches", vacancyId],
  vacancyRequirementsQueryKey: (vacancyId: string) => ["requirements", vacancyId]
}));

vi.mock("@/lib/ai-hiring-intelligence/hooks", () => ({
  useAiHiringIntelligenceQuery: () => hiringIntelligenceQuery()
}));

const passport: SkillPassportResponse = {
  total_skills: 3,
  total_evidence: 3,
  skills: [
    {
      id: "internal-skill-python",
      name: "Python",
      category: "language",
      evidence_confidence: 1,
      evidence_count: 2,
      evidence: [
        {
          id: "internal-evidence-id",
          title: "GitHub repository: example/project",
          description: "Python service evidence",
          source_type: "github_repository",
          source_reference: "https://github.com/example/project",
          evidence_confidence: 1
        },
        {
          id: "internal-resume-id",
          title: "RГ©sumГ©: profile.pdf",
          description: "Python experience",
          source_type: "resume",
          source_reference: "profile.pdf",
          evidence_confidence: 1
        }
      ],
      github_repositories: [
        {
          repository_name: "example/project",
          repository_url: "https://github.com/example/project",
          evidence_count: 1,
          repository_confidence: 61
        },
        {
          repository_name: "example/service",
          repository_url: "https://github.com/example/service",
          evidence_count: 1,
          repository_confidence: 22
        }
      ]
    },
    {
      id: "internal-skill-react",
      name: "React",
      category: "frontend",
      evidence_confidence: 0.8,
      evidence_count: 1,
      evidence: [{ id: "github-react", title: "Repository", description: null, source_type: "github_repository", source_reference: "https://github.com/example/project", evidence_confidence: 0.8 }],
      github_repositories: [
        {
          repository_name: "example/project",
          repository_url: "https://github.com/example/project",
          evidence_count: 1,
          repository_confidence: 55
        }
      ]
    },
    {
      id: "internal-skill-resume",
      name: "RГ©sumГ©-only skill",
      category: "backend",
      evidence_confidence: 0.5,
      evidence_count: 1,
      evidence: [{ id: "resume-only", title: "RГ©sumГ©", description: null, source_type: "resume", source_reference: "profile.pdf", evidence_confidence: 0.5 }],
      github_repositories: []
    }
  ]
};

function readyPassport(data: SkillPassportResponse = passport) {
  passportQuery.mockReturnValue({ data, isLoading: false, isError: false, refetch: vi.fn() });
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
describe("SkillPassportWorkspace", () => {
  it("renders confirmed skills with their existing confidence without internal IDs", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getAllByText("Confirmed")).toHaveLength(3);
    expect(document.body.textContent).not.toContain("internal-evidence-id");
    expect(document.body.textContent).not.toContain("internal-skill-python");
  });

  it("shows independent repository evidence only after opening the evidence dialog", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);

    expect(screen.queryByText("61% evidence in this repository")).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Open evidence" })[0]);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("example/project")).toBeInTheDocument();
    expect(within(dialog).getByText("61% evidence in this repository")).toBeInTheDocument();
    expect(within(dialog).getByText("22% evidence in this repository")).toBeInTheDocument();
    expect(within(dialog).getByText("Evidence in each repository is evaluated independently and does not add up to the overall confidence.")).toBeInTheDocument();
  });

  it("filters GitHub skills and hides rГ©sumГ©-only skills", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.click(screen.getByRole("button", { name: "GitHub" }));
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.queryByText("RГ©sumГ©-only skill")).not.toBeInTheDocument();
  });

  it("filters skills by search term", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.change(screen.getByRole("searchbox", { name: "Search confirmed skills" }), { target: { value: "react" } });
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.queryByText("Python")).not.toBeInTheDocument();
  });

  it("opens the evidence details for a skill", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.click(screen.getAllByRole("button", { name: "Open evidence" })[0]);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Source-specific evidence")).toBeInTheDocument();
    expect(within(dialog).getByRole("link", { name: "Open source" })).toHaveAttribute("href", "https://github.com/example/project");
  });

  it("shows the full empty state when no skills are confirmed", () => {
    readyPassport({ skills: [], total_skills: 0, total_evidence: 0 });
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("No verified skills yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Connect GitHub" })).toHaveAttribute("href", "/#github-section-title");
  });
});

describe("CandidateDashboardSection", () => {
  it("renders only the compact Skill Passport preview", () => {
    dashboardQuery.mockReturnValue({
      data: { github: { connected: true, repositories: 1 }, evidence: { count: 3 }, passport: { skills: 11, top_skills: ["Python", "React", "TypeScript"] }, roadmap: { items: 2 } },
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    });
    render(<CandidateDashboardSection enabled />);
    expect(screen.getByText("Top skills: Python, React, TypeScript")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Skill Passport" })).toHaveAttribute("href", "/skill-passport");
    expect(screen.queryByText("Evidence supporting Python")).not.toBeInTheDocument();
  });
});

describe("CandidateProfileView", () => {
  it("shows the existing match, evidence detail selection, and roadmap preview", () => {
    matchExplanationQuery.mockReturnValue({ isLoading: false, isError: true, data: null });
    hiringIntelligenceQuery.mockReturnValue({ isLoading: false, isError: true, data: null });
    matchDetailsQuery.mockReturnValue({
      data: {
        candidate: { id: "candidate-private-id", name: "Alex Morgan", headline: "Python Backend Developer", avatar: null },
        match: { score: 92, required: { matched: ["Python", "FastAPI"], missing: ["Redis"] }, preferred: { matched: ["Docker"], missing: ["Kubernetes"] } },
        passport: {
          top_skills: ["Python", "FastAPI", "Docker"],
          skills: [
            { name: "Python", evidence_confidence: 0.87, evidence_count: 3, source_types: ["github_repository", "resume"] },
            { name: "FastAPI", evidence_confidence: 0.83, evidence_count: 2, source_types: ["github_repository"] },
            { name: "Docker", evidence_confidence: 0.72, evidence_count: 1, source_types: ["github_repository"] }
          ]
        },
        evidence: [
          { source_type: "github_repository", title: "GitHub Repository", skills: ["Python", "FastAPI", "Docker"] },
          { source_type: "resume", title: "RГ©sumГ©", skills: ["Python", "FastAPI"] }
        ],
        roadmap: [
          { id: "roadmap-1", title: "Learn Redis", reason: "Missing Redis", priority: "high", missing_skills: ["Redis"], related_skills: [] },
          { id: "roadmap-2", title: "Learn Kubernetes", reason: "Missing Kubernetes", priority: "medium", missing_skills: ["Kubernetes"], related_skills: [] },
          { id: "roadmap-3", title: "Practice systems", reason: "Broaden skills", priority: "low", missing_skills: [], related_skills: [] },
          { id: "roadmap-4", title: "Advanced Docker", reason: "Build depth", priority: "low", missing_skills: [], related_skills: [] }
        ]
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    });
    render(<CandidateProfileView candidateId="candidate-private-id" vacancyId="vacancy-1" enabled />);
    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
    expect(screen.getByText("Vacancy match")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Skill Passport" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Python evidence confidence: 87 percent" })).toHaveAttribute("aria-valuenow", "87");
    expect(screen.getAllByText("Required · Matched")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute("href", "/employer/matches/candidate-private-id/ai-hiring?vacancy_id=vacancy-1");
    expect(screen.queryByText("Technical Interview Recommendation")).not.toBeInTheDocument();
    expect(screen.queryByText("AI analysis is temporarily unavailable.")).not.toBeInTheDocument();
    expect(screen.getAllByText("Partially matched")).toHaveLength(2);
    expect(screen.getAllByText("Redis")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "View evidence for Python" }));
    expect(screen.getByRole("button", { name: "Clear Python" })).toBeInTheDocument();
    expect(screen.getByText("GitHub Repository")).toBeInTheDocument();
    expect(screen.queryByText("Advanced Docker")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open Full Roadmap" }));
    expect(screen.getByText("Advanced Docker")).toBeInTheDocument();
  });
});

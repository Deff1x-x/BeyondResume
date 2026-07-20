import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { EmployerSection } from "@/features/employer-section";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import type { SkillPassportResponse } from "@/lib/api/types/skill-passport";

const passportQuery = vi.fn();
const dashboardQuery = vi.fn();
const employerCompanyQuery = vi.fn();
const employerVacanciesQuery = vi.fn();
const employerQueryResults = vi.fn();
const matchDetailsQuery = vi.fn();

vi.mock("@/lib/skill-passport/hooks", () => ({
  useSkillPassportQuery: () => passportQuery()
}));

vi.mock("@/lib/dashboard/hooks", () => ({
  useCandidateDashboardQuery: () => dashboardQuery()
}));

vi.mock("@tanstack/react-query", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-query")>()),
  useQueries: () => employerQueryResults()
}));

vi.mock("@/lib/employer/hooks", () => ({
  useAddVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerCompany: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerVacancy: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useDeleteVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useEmployerCompanyQuery: () => employerCompanyQuery(),
  useEmployerSkillsQuery: () => ({ data: [], isLoading: false, isError: false }),
  useEmployerVacanciesQuery: () => employerVacanciesQuery(),
  useEmployerVacancyQuery: () => ({ isLoading: false, isError: false, data: null }),
  useMatchDetailsQuery: () => matchDetailsQuery(),
  useVacancyMatchesQuery: () => ({ data: { matches: [] }, isLoading: false, isError: false }),
  useVacancyRequirementsQuery: () => ({ data: [], isLoading: false, isError: false }),
  vacancyMatchesQueryKey: (vacancyId: string) => ["matches", vacancyId],
  vacancyRequirementsQueryKey: (vacancyId: string) => ["requirements", vacancyId]
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
          title: "Résumé: profile.pdf",
          description: "Python experience",
          source_type: "resume",
          source_reference: "profile.pdf",
          evidence_confidence: 1
        }
      ]
    },
    {
      id: "internal-skill-react",
      name: "React",
      category: "frontend",
      evidence_confidence: 0.8,
      evidence_count: 1,
      evidence: [{ id: "github-react", title: "Repository", description: null, source_type: "github_repository", source_reference: "https://github.com/example/project", evidence_confidence: 0.8 }]
    },
    {
      id: "internal-skill-resume",
      name: "Résumé-only skill",
      category: "backend",
      evidence_confidence: 0.5,
      evidence_count: 1,
      evidence: [{ id: "resume-only", title: "Résumé", description: null, source_type: "resume", source_reference: "profile.pdf", evidence_confidence: 0.5 }]
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
  it("renders confirmed skills and their evidence counts without internal IDs", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("2 evidence units")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("internal-evidence-id");
    expect(document.body.textContent).not.toContain("internal-skill-python");
  });

  it("filters GitHub skills and hides résumé-only skills", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.click(screen.getByRole("button", { name: "GitHub" }));
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.queryByText("Résumé-only skill")).not.toBeInTheDocument();
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
    fireEvent.click(screen.getAllByRole("button", { name: "View evidence" })[0]);
    expect(screen.getByText("Evidence supporting Python")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open source" })).toHaveAttribute("href", "https://github.com/example/project");
  });

  it("shows the full empty state when no skills are confirmed", () => {
    readyPassport({ skills: [], total_skills: 0, total_evidence: 0 });
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("Build your evidence-based skill passport")).toBeInTheDocument();
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

describe("EmployerSection", () => {
  it("summarizes existing vacancies and candidate matches without new API data", () => {
    employerCompanyQuery.mockReturnValue({ data: { company_name: "Beyond", website: null, description: null }, isLoading: false, isError: false });
    employerVacanciesQuery.mockReturnValue({ data: [{ id: "vacancy-1", title: "Frontend Engineer", description: "Build product UI", status: "open", created_at: "2026-07-20T10:00:00Z" }], isLoading: false, isError: false, refetch: vi.fn() });
    employerQueryResults
      .mockReturnValueOnce([{ data: [{ id: "requirement-1" }] }])
      .mockReturnValueOnce([{ data: { matches: [{ candidate_id: "candidate-1", candidate_name: "Alex Morgan", score: 82, required: { matched: ["React"], missing: [] }, preferred: { matched: [], missing: [] } }] } }]);
    render(<EmployerSection enabled />);
    expect(screen.getByText("Active vacancies")).toBeInTheDocument();
    expect(screen.getAllByText("82%")).toHaveLength(2);
    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "+ Create Vacancy" })).toHaveAttribute("href", "#create-vacancy");
  });
});

describe("CandidateProfileView", () => {
  it("shows the existing match, evidence detail selection, and roadmap preview", () => {
    matchDetailsQuery.mockReturnValue({
      data: {
        candidate: { id: "candidate-private-id", name: "Alex Morgan", headline: "Python Backend Developer", avatar: null },
        match: { score: 92, required: { matched: ["Python", "FastAPI"], missing: ["Redis"] }, preferred: { matched: ["Docker"], missing: ["Kubernetes"] } },
        passport: { top_skills: ["Python", "FastAPI", "Docker"] },
        evidence: [
          { source_type: "github_repository", title: "GitHub Repository", skills: ["Python", "FastAPI", "Docker"] },
          { source_type: "resume", title: "Résumé", skills: ["Python", "FastAPI"] }
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

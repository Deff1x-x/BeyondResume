import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import type { SkillPassportResponse } from "@/lib/api/types/skill-passport";

const passportQuery = vi.fn();
const dashboardQuery = vi.fn();

vi.mock("@/lib/skill-passport/hooks", () => ({
  useSkillPassportQuery: () => passportQuery()
}));

vi.mock("@/lib/dashboard/hooks", () => ({
  useCandidateDashboardQuery: () => dashboardQuery()
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

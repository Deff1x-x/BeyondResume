import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import type {
  SkillPassportEvidence,
  SkillPassportResponse,
  SkillPassportSkill
} from "@/lib/api/types/skill-passport";

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
  useVacancyShortlistQuery: () => ({
    data: { entries: [] },
    isLoading: false,
    isError: false,
    isSuccess: true
  }),
  useSaveCandidateToShortlist: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  }),
  useRemoveCandidateFromShortlist: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  }),
  useUpdateEmployerShortlistStage: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  }),
  vacancyMatchesQueryKey: (vacancyId: string) => ["matches", vacancyId],
  vacancyRequirementsQueryKey: (vacancyId: string) => ["requirements", vacancyId]
}));

vi.mock("@/lib/ai-hiring-intelligence/hooks", () => ({
  useAiHiringIntelligenceQuery: () => hiringIntelligenceQuery()
}));

function evidence(
  overrides: Partial<SkillPassportEvidence> & Pick<SkillPassportEvidence, "id" | "source_type">
): SkillPassportEvidence {
  return {
    title: null,
    description: null,
    source_reference: null,
    verification_status: null,
    ownership_status: null,
    evidence_confidence: 0,
    ...overrides
  };
}

function skill(
  overrides: Partial<SkillPassportSkill> & Pick<SkillPassportSkill, "id" | "name">
): SkillPassportSkill {
  return {
    category: "language",
    evidence_confidence: 0.5,
    evidence_count: 0,
    evidence: [],
    github_repositories: [],
    ...overrides
  };
}

const passport: SkillPassportResponse = {
  total_skills: 3,
  total_evidence: 3,
  skills: [
    skill({
      id: "internal-skill-python",
      name: "Python",
      category: "language",
      evidence_confidence: 1,
      evidence_count: 2,
      evidence: [
        evidence({
          id: "internal-evidence-id",
          title: "GitHub repository: example/project",
          description: "Python service evidence",
          source_type: "github_repository",
          source_reference: "https://github.com/example/project",
          verification_status: "source_reachable",
          ownership_status: "unverified",
          evidence_confidence: 1
        }),
        evidence({
          id: "internal-resume-id",
          title: "Resume: profile.pdf",
          description: "Python experience",
          source_type: "resume",
          source_reference: "profile.pdf",
          verification_status: "unverified",
          ownership_status: "unverified",
          evidence_confidence: 1
        })
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
    }),
    skill({
      id: "internal-skill-react",
      name: "React",
      category: "frontend",
      evidence_confidence: 0.8,
      evidence_count: 1,
      evidence: [
        evidence({
          id: "github-react",
          title: "Repository",
          source_type: "github_repository",
          source_reference: "https://github.com/example/project",
          verification_status: "source_reachable",
          ownership_status: "unverified",
          evidence_confidence: 0.8
        })
      ],
      github_repositories: [
        {
          repository_name: "example/project",
          repository_url: "https://github.com/example/project",
          evidence_count: 1,
          repository_confidence: 55
        }
      ]
    }),
    skill({
      id: "internal-skill-resume",
      name: "Resume-only skill",
      category: "backend",
      evidence_confidence: 0.5,
      evidence_count: 1,
      evidence: [
        evidence({
          id: "resume-only",
          title: "Resume",
          source_type: "resume",
          source_reference: "profile.pdf",
          verification_status: "unverified",
          ownership_status: "unverified",
          evidence_confidence: 0.5
        })
      ]
    })
  ]
};

function readyPassport(data: SkillPassportResponse = passport) {
  passportQuery.mockReturnValue({ data, isLoading: false, isError: false, refetch: vi.fn() });
}

function openFirstEvidenceDialog() {
  fireEvent.click(screen.getAllByRole("button", { name: "Open evidence" })[0]);
  return screen.getByRole("dialog");
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("SkillPassportWorkspace", () => {
  it("renders passport skills with aggregate evidence strength without internal IDs", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("Skills in your passport")).toBeInTheDocument();
    expect(screen.queryByText("Confirmed")).not.toBeInTheDocument();
    expect(document.body.textContent).not.toContain("internal-evidence-id");
    expect(document.body.textContent).not.toContain("internal-skill-python");
  });

  it("shows independent repository evidence only after opening the evidence dialog", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);

    expect(screen.queryByText("61% evidence in this repository")).not.toBeInTheDocument();
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getByText("example/project")).toBeInTheDocument();
    expect(within(dialog).getByText("61% evidence in this repository")).toBeInTheDocument();
    expect(within(dialog).getByText("22% evidence in this repository")).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        "Evidence in each repository is evaluated independently and does not add up to the overall confidence."
      )
    ).toBeInTheDocument();
  });

  it("filters GitHub skills and hides resume-only skills", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.click(screen.getByRole("button", { name: "GitHub" }));
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.queryByText("Resume-only skill")).not.toBeInTheDocument();
  });

  it("filters skills by search term", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.change(screen.getByRole("searchbox", { name: "Search skills" }), {
      target: { value: "react" }
    });
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.queryByText("Python")).not.toBeInTheDocument();
  });

  it("shows no matching skills when filters exclude everything", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    fireEvent.change(screen.getByRole("searchbox", { name: "Search skills" }), {
      target: { value: "zzzz-missing" }
    });
    expect(screen.getByText("No matching skills")).toBeInTheDocument();
  });

  it("opens the evidence details and keeps only https source links", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getByText("Source-specific evidence")).toBeInTheDocument();
    expect(within(dialog).getByText("Supporting evidence")).toBeInTheDocument();
    expect(within(dialog).getByRole("link", { name: "Open source" })).toHaveAttribute(
      "href",
      "https://github.com/example/project"
    );
    expect(within(dialog).queryByText("profile.pdf")).not.toBeInTheDocument();
  });

  it("closes the evidence dialog", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getByText("Supporting evidence")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "Close" }));
    expect(screen.queryByText("Supporting evidence")).not.toBeInTheDocument();
  });

  it("shows the empty state when the Skill Passport has no skills", () => {
    readyPassport({ skills: [], total_skills: 0, total_evidence: 0 });
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("No skills in your Skill Passport yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Connect GitHub" })).toHaveAttribute(
      "href",
      "/#github-section-title"
    );
  });

  it("shows loading and error retry states", () => {
    const refetch = vi.fn();
    passportQuery.mockReturnValue({ data: undefined, isLoading: true, isError: false, refetch });
    const { rerender } = render(<SkillPassportWorkspace />);
    expect(screen.getByRole("status", { name: "Loading skill passport" })).toBeInTheDocument();

    passportQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("boom"),
      refetch
    });
    rerender(<SkillPassportWorkspace />);
    expect(screen.getByText("Skill Passport unavailable")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalled();
  });

  it("avoids verified/confirmed ownership claims in Skill Passport copy", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    expect(screen.getByText("Explore skills supported by your evidence")).toBeInTheDocument();
    expect(screen.queryByText("Confirmed")).not.toBeInTheDocument();
    expect(screen.queryByText("Confirmed skills")).not.toBeInTheDocument();
    expect(screen.queryByText(/verified skills/i)).not.toBeInTheDocument();
    expect(screen.queryByText("No verified skills yet")).not.toBeInTheDocument();
    expect(screen.queryByText("Explore confirmed skills")).not.toBeInTheDocument();
  });
});

describe("SkillPassportWorkspace evidence explainability", () => {
  it("shows known verification and ownership labels as separate badges", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getByText("Source reachable")).toBeInTheDocument();
    expect(within(dialog).getAllByText("Ownership unverified").length).toBeGreaterThan(0);
    expect(within(dialog).getByText("Unverified")).toBeInTheDocument();
    expect(within(dialog).queryByText("Verified")).not.toBeInTheDocument();
  });

  it("hides nullable and unknown trust statuses", () => {
    readyPassport({
      total_skills: 1,
      total_evidence: 2,
      skills: [
        skill({
          id: "skill-null",
          name: "Null Trust Skill",
          evidence_confidence: 0.4,
          evidence_count: 2,
          evidence: [
            evidence({
              id: "null-statuses",
              title: "Null statuses",
              source_type: "resume",
              verification_status: null,
              ownership_status: null,
              evidence_confidence: 0.4
            }),
            evidence({
              id: "unknown-statuses",
              title: "Unknown statuses",
              source_type: "resume",
              verification_status: "future_unknown_status",
              ownership_status: "mystery_ownership",
              evidence_confidence: 0.4
            })
          ]
        })
      ]
    });
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).queryByText("future_unknown_status")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("mystery_ownership")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("Unverified")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("Ownership unverified")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("Source reachable")).not.toBeInTheDocument();
  });

  it("maps source labels without leaking raw source keys", () => {
    readyPassport({
      total_skills: 1,
      total_evidence: 3,
      skills: [
        skill({
          id: "skill-sources",
          name: "Source Labels",
          evidence_confidence: 0.7,
          evidence_count: 3,
          evidence: [
            evidence({
              id: "gh",
              title: "GitHub unit",
              source_type: "github_repository",
              verification_status: "source_reachable",
              ownership_status: "unverified",
              evidence_confidence: 0.7
            }),
            evidence({
              id: "cv",
              title: "Resume unit",
              source_type: "resume",
              verification_status: "unverified",
              ownership_status: "unverified",
              evidence_confidence: 0.5
            }),
            evidence({
              id: "unknown-source",
              title: "Unknown source unit",
              source_type: "portfolio_source",
              verification_status: null,
              ownership_status: null,
              evidence_confidence: 0.2
            })
          ]
        })
      ]
    });
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getAllByText("GitHub").length).toBeGreaterThan(0);
    expect(within(dialog).getAllByText("Resume").length).toBeGreaterThan(0);
    expect(within(dialog).getAllByText("Evidence").length).toBeGreaterThan(0);
    expect(within(dialog).queryByText("github_repository")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("portfolio_source")).not.toBeInTheDocument();
  });

  it("formats evidence strength for 0, fractional, and 1 confidence", () => {
    readyPassport({
      total_skills: 1,
      total_evidence: 3,
      skills: [
        skill({
          id: "skill-strength",
          name: "Strength Skill",
          evidence_confidence: 0.5,
          evidence_count: 3,
          evidence: [
            evidence({
              id: "zero",
              title: "Zero strength",
              source_type: "resume",
              evidence_confidence: 0
            }),
            evidence({
              id: "fraction",
              title: "Fractional strength",
              source_type: "resume",
              evidence_confidence: 0.06
            }),
            evidence({
              id: "full",
              title: "Full strength",
              source_type: "resume",
              evidence_confidence: 1
            })
          ]
        })
      ]
    });
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getByLabelText("Evidence strength 0 percent")).toHaveTextContent(
      "Evidence strength: 0%"
    );
    expect(within(dialog).getByLabelText("Evidence strength 6 percent")).toHaveTextContent(
      "Evidence strength: 6%"
    );
    expect(within(dialog).getByLabelText("Evidence strength 100 percent")).toHaveTextContent(
      "Evidence strength: 100%"
    );
  });

  it("keeps Resume and GitHub evidence parity for trust vocabulary", () => {
    readyPassport();
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    const githubUnit = within(dialog).getByText("GitHub repository: example/project").closest("li");
    const resumeUnit = within(dialog).getByText("Resume: profile.pdf").closest("li");
    expect(githubUnit).not.toBeNull();
    expect(resumeUnit).not.toBeNull();
    expect(within(githubUnit!).getByText("GitHub")).toBeInTheDocument();
    expect(within(resumeUnit!).getByText("Resume")).toBeInTheDocument();
    expect(within(githubUnit!).getByText("Source reachable")).toBeInTheDocument();
    expect(within(resumeUnit!).getByText("Unverified")).toBeInTheDocument();
    expect(within(githubUnit!).getByText("Ownership unverified")).toBeInTheDocument();
    expect(within(resumeUnit!).getByText("Ownership unverified")).toBeInTheDocument();
    expect(within(githubUnit!).queryByText("Verified")).not.toBeInTheDocument();
    expect(within(githubUnit!).getByLabelText("Evidence strength 100 percent")).toBeInTheDocument();
    expect(within(resumeUnit!).getByLabelText("Evidence strength 100 percent")).toBeInTheDocument();
  });

  it("keeps internal privacy tokens out of the Skill Passport DOM", () => {
    readyPassport({
      total_skills: 1,
      total_evidence: 1,
      skills: [
        skill({
          id: "privacy-skill",
          name: "Privacy Skill",
          evidence_confidence: 0.3,
          evidence_count: 1,
          evidence: [
            evidence({
              id: "privacy-evidence",
              title: "Public title only",
              description: "Candidate-private description is allowed",
              source_type: "github_repository",
              source_reference: "secret.config.json",
              verification_status: "source_reachable",
              ownership_status: "unverified",
              evidence_confidence: 0.3
            })
          ]
        })
      ]
    });
    render(<SkillPassportWorkspace />);
    openFirstEvidenceDialog();
    for (const token of [
      "github_repository",
      "source_import",
      "dependency_manifest",
      "rule_id",
      "matched_value",
      "secret.config.json"
    ]) {
      expect(document.body.textContent).not.toContain(token);
    }
  });

  it("handles missing title and description without inventing source links", () => {
    readyPassport({
      total_skills: 1,
      total_evidence: 1,
      skills: [
        skill({
          id: "minimal-skill",
          name: "Minimal Skill",
          evidence_confidence: 0,
          evidence_count: 1,
          evidence: [
            evidence({
              id: "minimal-evidence",
              source_type: "resume",
              evidence_confidence: 0
            })
          ]
        })
      ]
    });
    render(<SkillPassportWorkspace />);
    const dialog = openFirstEvidenceDialog();
    expect(within(dialog).getAllByText("Resume").length).toBeGreaterThan(0);
    expect(within(dialog).getByLabelText("Evidence strength 0 percent")).toBeInTheDocument();
    expect(within(dialog).queryByRole("link", { name: "Open source" })).not.toBeInTheDocument();
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
    expect(screen.getByText("Requirement coverage")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Based on vacancy requirements and skills in the candidate’s Skill Passport"
      )
    ).toBeInTheDocument();
    expect(screen.queryByText("Vacancy match")).not.toBeInTheDocument();
    expect(screen.queryByText(/verified skills/i)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Evidence across Skill Passport" })).toBeInTheDocument();
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

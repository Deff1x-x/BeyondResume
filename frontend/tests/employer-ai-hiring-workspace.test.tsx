import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AiHiringWorkspace } from "@/features/match-details/ai-hiring-workspace";

const detailsQuery = vi.fn();
const intelligenceQuery = vi.fn();

vi.mock("@/lib/employer/hooks", () => ({
  useMatchDetailsQuery: () => detailsQuery()
}));
vi.mock("@/lib/ai-hiring-intelligence/hooks", () => ({
  useAiHiringIntelligenceQuery: () => intelligenceQuery()
}));

const details = {
  candidate: { id: "candidate-1", name: "Alex Morgan", headline: "Backend Engineer", avatar: null },
  match: { score: 82, required: { matched: ["Python"], missing: ["Redis"] }, preferred: { matched: [], missing: [] } },
  passport: { top_skills: ["Python"], skills: [{ name: "Python", evidence_confidence: 0.87, evidence_count: 2, source_types: ["github_repository"] }] },
  evidence: [],
  roadmap: []
};

afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("AiHiringWorkspace", () => {
  it("renders AI Hiring in the preserved candidate and vacancy context", () => {
    detailsQuery.mockReturnValue({ data: details, isLoading: false, isError: false });
    intelligenceQuery.mockReturnValue({ isLoading: false, isError: false, data: { verdict: { technical_interview_recommendation: "recommended", confidence: 81, summary: "Evidence supports a technical interview.", strengths: ["Python evidence"], concerns: ["Limited Redis evidence"] }, interview_questions: [{ skill: "Python", difficulty: "medium", question: "Explain dependency injection.", reason: "Confirmed evidence." }] } });

    render(<AiHiringWorkspace candidateId="candidate-1" vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByText("Vacancy match 82%")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Candidate Review" })).toHaveAttribute("href", "/employer/matches/candidate-1?vacancy_id=vacancy-1");
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute("href", "/employer/matches/candidate-1/ai-hiring?vacancy_id=vacancy-1");
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Technical Interview Recommendation")).toBeInTheDocument();
    expect(screen.getByText("AI-generated analysis")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "AI Explanation" })).not.toBeInTheDocument();
    expect(screen.getByText("Use this analysis as supporting information, not as the sole basis for a hiring decision.")).toBeInTheDocument();
    expect(intelligenceQuery).toHaveBeenCalledTimes(1);
  });

  it("keeps a failed AI request separate from candidate context", () => {
    detailsQuery.mockReturnValue({ data: details, isLoading: false, isError: false });
    intelligenceQuery.mockReturnValue({ isLoading: false, isError: true, data: undefined, error: { status: 503 }, refetch: vi.fn() });

    render(<AiHiringWorkspace candidateId="candidate-1" vacancyId="vacancy-1" enabled />);
    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByText("AI analysis is temporarily unavailable.")).toBeInTheDocument();
    expect(screen.getByText("Vacancy match 82%")).toBeInTheDocument();
  });
});

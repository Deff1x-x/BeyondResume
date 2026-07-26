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
  roadmap: [],
  has_applied: true
};

const intelligence = {
  verdict: "hire",
  confidence: 81,
  executive_summary: "The supplied evidence supports moving forward with this candidate.",
  strengths: ["Python evidence"],
  hiring_risks: ["Limited Redis evidence"],
  confidence_explanation: ["Python experience is supported by verified evidence"],
  first_90_days_focus: ["Build familiarity with the existing service architecture"],
  recommended_next_action: "Proceed to the next hiring stage."
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("AiHiringWorkspace", () => {
  it("renders AI Hiring in the preserved candidate and vacancy context", () => {
    detailsQuery.mockReturnValue({ data: details, isLoading: false, isError: false });
    intelligenceQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: intelligence
    });

    render(<AiHiringWorkspace candidateId="candidate-1" vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByText("Vacancy match 82%")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Candidate Review" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/ai-hiring?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("heading", { name: "AI Hiring Intelligence" })).toBeInTheDocument();
    expect(screen.getByText("AI-generated analysis")).toBeInTheDocument();
    expect(screen.getByLabelText("Recommendation: Hire")).toHaveTextContent("Hire");
    expect(screen.getByLabelText("Top skills")).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Required matched").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Required missing").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Limited Redis evidence")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Interview Questions" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Explain dependency injection/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "AI Explanation" })).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Use this analysis as supporting information, not as the sole basis for a hiring decision."
      )
    ).toBeInTheDocument();
    expect(intelligenceQuery).toHaveBeenCalledTimes(1);
  });

  it("dedupes top skills and keeps match counts aligned to details", () => {
    detailsQuery.mockReturnValue({
      data: {
        ...details,
        passport: { ...details.passport, top_skills: ["Python", "Python", "Docker", ""] },
        match: {
          score: 70,
          required: { matched: ["Python", "SQL"], missing: ["Redis", "Kafka"] },
          preferred: { matched: [], missing: [] }
        }
      },
      isLoading: false,
      isError: false
    });
    intelligenceQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: intelligence
    });

    render(<AiHiringWorkspace candidateId="candidate-1" vacancyId="vacancy-1" enabled />);

    expect(screen.getAllByText("Python")).toHaveLength(1);
    expect(screen.getByText("Docker")).toBeInTheDocument();
    expect(screen.getByText("Required matched").parentElement).toHaveTextContent("2");
    expect(screen.getByText("Required missing").parentElement).toHaveTextContent("2");
    expect(intelligenceQuery).toHaveBeenCalledTimes(1);
  });

  it("keeps a failed AI request separate from candidate context", () => {
    detailsQuery.mockReturnValue({ data: details, isLoading: false, isError: false });
    intelligenceQuery.mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: { status: 503 },
      refetch: vi.fn()
    });

    render(<AiHiringWorkspace candidateId="candidate-1" vacancyId="vacancy-1" enabled />);
    expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    expect(screen.getByText("AI analysis is temporarily unavailable.")).toBeInTheDocument();
    expect(screen.getByText("Vacancy match 82%")).toBeInTheDocument();
  });
});

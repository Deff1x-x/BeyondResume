import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AiHiringIntelligenceSection } from "@/features/ai-hiring-intelligence-section";

const query = vi.fn();
vi.mock("@/lib/ai-hiring-intelligence/hooks", () => ({ useAiHiringIntelligenceQuery: () => query() }));

afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("AiHiringIntelligenceSection", () => {
  it("renders an accessible loading state", () => {
    query.mockReturnValue({ isLoading: true });
    render(<AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />);
    expect(screen.getByRole("status")).toHaveTextContent("Generating AI analysis...");
  });

  it("renders the interview-oriented verdict and questions without raw enum text", () => {
    query.mockReturnValue({ isLoading: false, isError: false, data: { verdict: { technical_interview_recommendation: "recommended", confidence: 87, summary: "Evidence supports a technical interview.", strengths: ["Python evidence"], concerns: ["Limited Docker evidence"] }, interview_questions: [{ skill: "Python", difficulty: "medium", question: "Explain dependency injection.", reason: "Confirmed project evidence." }] } });
    render(<AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />);
    expect(screen.getByRole("heading", { name: "Technical Interview Verdict" })).toBeInTheDocument();
    expect(screen.getByText("Recommended for technical interview")).toBeInTheDocument();
    expect(screen.getByText("87% confidence")).toBeInTheDocument();
    expect(screen.getByText("Python evidence")).toBeInTheDocument();
    expect(screen.getByText("Limited Docker evidence")).toBeInTheDocument();
    expect(screen.getByText("Explain dependency injection.")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("recommended");
  });

  it("renders unavailable state without crashing", () => {
    query.mockReturnValue({ isLoading: false, isError: true, data: undefined });
    render(<AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />);
    expect(screen.getByRole("status")).toHaveTextContent("AI analysis is temporarily unavailable.");
  });
});

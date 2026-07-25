import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AiHiringIntelligenceSection } from "@/features/ai-hiring-intelligence-section";
import type { AiHiringIntelligence } from "@/lib/api/types/ai-hiring-intelligence";

const query = vi.fn();
vi.mock("@/lib/ai-hiring-intelligence/hooks", () => ({
  useAiHiringIntelligenceQuery: () => query()
}));

const sample: AiHiringIntelligence = {
  verdict: "hire",
  confidence: 87,
  executive_summary: "The supplied evidence supports moving forward with this candidate.",
  strengths: ["Python evidence"],
  hiring_risks: ["Limited Docker evidence"],
  confidence_explanation: ["Python experience is supported by verified evidence"],
  first_90_days_focus: ["Build familiarity with the existing service architecture"],
  recommended_next_action: "Proceed to the next hiring stage."
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("AiHiringIntelligenceSection", () => {
  it("renders an accessible loading state", () => {
    query.mockReturnValue({ isLoading: true });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(screen.getByRole("status")).toHaveTextContent("Generating AI analysis...");
  });

  it("renders the executive hiring decision without interview content or raw enum text", () => {
    query.mockReturnValue({ isLoading: false, isError: false, data: sample });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.getByRole("heading", { name: "AI Hiring Intelligence" })).toBeInTheDocument();
    expect(screen.getByText("AI Recommendation")).toBeInTheDocument();
    expect(screen.getByLabelText("Recommendation: Hire")).toHaveTextContent("Hire");
    expect(screen.getByLabelText("87% confidence")).toHaveTextContent("87%");
    expect(screen.getByRole("heading", { name: "Executive summary" })).toBeInTheDocument();
    expect(screen.getByText(sample.executive_summary)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Strengths" })).toBeInTheDocument();
    expect(screen.getByText("Python evidence")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hiring risks" })).toBeInTheDocument();
    expect(screen.getByText("Limited Docker evidence")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Confidence" })).toBeInTheDocument();
    expect(
      screen.getByText("Python experience is supported by verified evidence")
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "First 90 days" })).toBeInTheDocument();
    expect(
      screen.getByText("Build familiarity with the existing service architecture")
    ).toBeInTheDocument();
    expect(screen.getByText("Proceed to the next hiring stage.")).toBeInTheDocument();

    expect(screen.queryByRole("heading", { name: "Interview Questions" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Interview Questions/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Explain dependency injection/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/technical interview/i)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toContain("strong_hire");
    expect(document.body.textContent).not.toContain("do_not_hire");
    expect(document.body.textContent).not.toContain("insufficient_evidence");
    expect(document.body.textContent).not.toContain("interview_questions");
  });

  it("renders labels for every hiring verdict and confidence bounds", () => {
    const verdicts: Array<{ verdict: AiHiringIntelligence["verdict"]; label: string }> = [
      { verdict: "strong_hire", label: "Strong hire" },
      { verdict: "hire", label: "Hire" },
      { verdict: "consider", label: "Consider" },
      { verdict: "insufficient_evidence", label: "Insufficient evidence" },
      { verdict: "do_not_hire", label: "Do not hire" }
    ];

    for (const entry of verdicts) {
      cleanup();
      query.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { ...sample, verdict: entry.verdict, confidence: 0 }
      });
      render(
        <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
      );
      expect(screen.getByLabelText(`Recommendation: ${entry.label}`)).toHaveTextContent(entry.label);
      expect(screen.getByLabelText("0% confidence")).toHaveTextContent("0%");
      if (entry.verdict.includes("_")) {
        expect(document.body.textContent).not.toContain(entry.verdict);
      }
    }

    cleanup();
    query.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { ...sample, confidence: 100 }
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(screen.getByLabelText("100% confidence")).toHaveTextContent("100%");
  });

  it("keeps unknown verdicts from breaking the recommendation card", () => {
    query.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { ...sample, verdict: "unexpected_verdict" as AiHiringIntelligence["verdict"] }
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(screen.getByLabelText("Recommendation: Evidence review")).toHaveTextContent(
      "Evidence review"
    );
    expect(document.body.textContent).not.toContain("unexpected_verdict");
  });

  it("renders duplicate list items without relying on value-only keys", () => {
    query.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        ...sample,
        strengths: ["Repeated strength", "Repeated strength"],
        hiring_risks: ["Repeated risk", "Repeated risk"]
      }
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(screen.getAllByText("Repeated strength")).toHaveLength(2);
    expect(screen.getAllByText("Repeated risk")).toHaveLength(2);
  });

  it("omits empty optional insight sections instead of empty cards", () => {
    query.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        ...sample,
        strengths: [],
        hiring_risks: [],
        confidence_explanation: [],
        first_90_days_focus: []
      }
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.queryByRole("heading", { name: "Strengths" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Hiring risks" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Confidence" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "First 90 days" })).not.toBeInTheDocument();
    expect(screen.queryByText("No clear strengths identified")).not.toBeInTheDocument();
    expect(screen.queryByText("No significant hiring risks identified")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Executive summary" })).toBeInTheDocument();
    expect(screen.getByText(sample.executive_summary)).toBeInTheDocument();
  });

  it("renders unavailable state and keeps retry", () => {
    const refetch = vi.fn();
    query.mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: { status: 503 },
      refetch
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "AI analysis is temporarily unavailable."
    );
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("wraps long plain-text content safely", () => {
    const longSummary = `${"Long summary sentence. ".repeat(20)}Tail marker.`;
    query.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        ...sample,
        executive_summary: longSummary,
        recommended_next_action: "Keep reviewing alternatives while gathering more evidence."
      }
    });
    render(
      <AiHiringIntelligenceSection candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(
      screen.getByText((_, node) => node?.tagName === "P" && node.textContent === longSummary)
    ).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});

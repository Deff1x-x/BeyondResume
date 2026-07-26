import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AiCandidateCompareSection } from "@/features/employer/ai-candidate-compare-section";
import {
  CandidateComparisonView
} from "@/features/employer/candidate-comparison-view";
import { ApiClientError } from "@/lib/api/error";
import type { AiCandidateCompareResponse } from "@/lib/api/types/ai-candidate-compare";
import type {
  EmployerShortlistEntry,
  VacancyMatch
} from "@/lib/api/types/employer";

const postVacancyAiCompare = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/ai-candidate-compare", () => ({
  postVacancyAiCompare: (...args: unknown[]) => postVacancyAiCompare(...args)
}));

const shortlistQuery = vi.hoisted(() => vi.fn());
const matchesQuery = vi.hoisted(() => vi.fn());

vi.mock("@/lib/employer/hooks", () => ({
  useVacancyShortlistQuery: () => shortlistQuery(),
  useVacancyMatchesQuery: () => matchesQuery()
}));

function sampleResponse(
  overrides: Partial<AiCandidateCompareResponse> = {}
): AiCandidateCompareResponse {
  return {
    vacancy_id: "vacancy-1",
    candidate_ids: ["candidate-1", "candidate-2"],
    generation_mode: "live",
    summary: "Candidate A covers more required skills than Candidate B.",
    candidate_assessments: [
      {
        candidate_id: "candidate-1",
        strengths: [{ text: "Strong TypeScript coverage.", fact_refs: ["f1"] }],
        risks: [{ text: "Missing GraphQL evidence.", fact_refs: ["f2"] }]
      },
      {
        candidate_id: "candidate-2",
        strengths: [{ text: "Broader preferred skills.", fact_refs: ["f3"] }],
        risks: [{ text: "Lower required coverage.", fact_refs: ["f4"] }]
      }
    ],
    key_differences: [
      { text: "Required skill coverage differs.", fact_refs: ["f1", "f4"] }
    ],
    interview_focus_questions: [
      {
        question: "Describe a TypeScript service you owned.",
        candidate_ids: ["candidate-1"],
        fact_refs: ["f1"]
      }
    ],
    recommended_candidate_id: "candidate-1",
    hiring_recommendation: {
      why_leads: [
        {
          text: "Stronger required coverage in supplied facts.",
          fact_refs: ["f1"]
        }
      ],
      main_risk: {
        text: "Missing GraphQL evidence still needs interview validation.",
        fact_refs: ["f2"]
      },
      interview_focus: [
        {
          text: "TypeScript service ownership",
          fact_refs: ["f1"]
        },
        {
          text: "GraphQL delivery experience",
          fact_refs: ["f2"]
        }
      ],
      alternative_outcome: {
        text: "If GraphQL ownership cannot be confirmed, Bea Chen becomes the stronger candidate.",
        fact_refs: ["f2", "f3"]
      }
    },
    confidence: "medium",
    uncertainties: [
      { text: "Evidence depth remains limited.", fact_refs: ["f1"] }
    ],
    ...overrides
  };
}

function entry(
  candidateId: string,
  overrides: Partial<EmployerShortlistEntry> = {}
): EmployerShortlistEntry {
  return {
    id: `shortlist-${candidateId}`,
    vacancy_id: "vacancy-1",
    candidate_id: candidateId,
    stage: "shortlisted",
    note: null,
    created_at: "2026-07-20T10:00:00Z",
    updated_at: "2026-07-20T10:00:00Z",
    ...overrides
  };
}

const matches: VacancyMatch[] = [
  {
    candidate_id: "candidate-1",
    candidate_name: "Alex Morgan",
    score: 82,
    required: { matched: ["TypeScript"], missing: ["GraphQL"] },
    preferred: { matched: ["CSS"], missing: [] }
  },
  {
    candidate_id: "candidate-2",
    candidate_name: "Bea Chen",
    score: 74,
    required: { matched: ["TypeScript"], missing: [] },
    preferred: { matched: ["CSS", "GraphQL"], missing: [] }
  }
];

function renderSection(
  props: {
    candidateIds?: string[];
    names?: Map<string, string>;
    enabled?: boolean;
  } = {}
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  const names =
    props.names ??
    new Map([
      ["candidate-1", "Alex Morgan"],
      ["candidate-2", "Bea Chen"]
    ]);
  return render(
    <QueryClientProvider client={client}>
      <AiCandidateCompareSection
        vacancyId="vacancy-1"
        candidateIds={props.candidateIds ?? ["candidate-1", "candidate-2"]}
        candidateNamesById={names}
        enabled={props.enabled ?? true}
      />
    </QueryClientProvider>
  );
}

describe("AiCandidateCompareSection", () => {
  beforeEach(() => {
    postVacancyAiCompare.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("does not request AI comparison before the button is clicked", () => {
    renderSection();
    expect(postVacancyAiCompare).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Generate AI comparison" })).toBeEnabled();
    expect(screen.queryByText(/Summary/i)).not.toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Verified Skills")).toBeInTheDocument();
    expect(screen.getByText("Candidate Match")).toBeInTheDocument();
    expect(screen.getByText("AI Insight")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
  });

  it("shows loading then live success without Demo AI", async () => {
    let resolveRequest: ((value: AiCandidateCompareResponse) => void) | undefined;
    postVacancyAiCompare.mockImplementation(
      () =>
        new Promise<AiCandidateCompareResponse>((resolve) => {
          resolveRequest = resolve;
        })
    );

    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));

    expect(await screen.findByText("Generating AI comparison…")).toBeInTheDocument();
    expect(screen.getByText("Generating")).toBeInTheDocument();
    expect(postVacancyAiCompare).toHaveBeenCalledTimes(1);
    expect(postVacancyAiCompare).toHaveBeenCalledWith("vacancy-1", {
      candidate_ids: ["candidate-1", "candidate-2"]
    });

    resolveRequest?.(sampleResponse({ generation_mode: "live" }));

    expect(await screen.findByText(/Candidate A covers more required skills/)).toBeInTheDocument();
    expect(screen.getByLabelText("Assessment for Alex Morgan")).toBeInTheDocument();
    expect(screen.getByLabelText("Assessment for Bea Chen")).toBeInTheDocument();
    expect(screen.getByText("Strong TypeScript coverage.")).toBeInTheDocument();
    expect(screen.getByText("Required skill coverage differs.")).toBeInTheDocument();
    expect(screen.getByText("Describe a TypeScript service you owned.")).toBeInTheDocument();
    expect(screen.getByText(/Advisory only/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Demo AI")).not.toBeInTheDocument();
  });

  it("shows Demo AI indicator for mock generation mode", async () => {
    postVacancyAiCompare.mockResolvedValue(sampleResponse({ generation_mode: "mock" }));
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(await screen.findByLabelText("Demo AI")).toBeInTheDocument();
    expect(screen.getByText("Demo AI")).toBeInTheDocument();
  });

  it("renders a structured hiring recommendation card for the current leader", async () => {
    postVacancyAiCompare.mockResolvedValue(sampleResponse({ confidence: "low" }));
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(await screen.findByText("Hiring Recommendation")).toBeInTheDocument();
    expect(screen.getByText("Current Leader")).toBeInTheDocument();
    const recommendation = screen.getByRole("region", { name: "Hiring Recommendation" });
    expect(recommendation).toHaveTextContent("Alex Morgan");
    expect(recommendation).toHaveTextContent("Low");
    expect(recommendation).toHaveTextContent("Stronger required coverage in supplied facts.");
    expect(recommendation).toHaveTextContent(
      "Missing GraphQL evidence still needs interview validation."
    );
    expect(recommendation).toHaveTextContent("TypeScript service ownership");
    expect(recommendation).toHaveTextContent(
      "If GraphQL ownership cannot be confirmed, Bea Chen becomes the stronger candidate."
    );
    expect(screen.queryByText("No clear recommendation")).not.toBeInTheDocument();
  });

  it("maps candidate ids to local names and never invents client pseudo-AI text", async () => {
    postVacancyAiCompare.mockResolvedValue(sampleResponse());
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(await screen.findByLabelText("Assessment for Alex Morgan")).toBeInTheDocument();
    expect(screen.getByLabelText("Assessment for Bea Chen")).toBeInTheDocument();
    expect(screen.queryByText(/pseudo/i)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toContain("client-generated");
  });

  it("shows unavailable state and supports manual retry", async () => {
    postVacancyAiCompare
      .mockRejectedValueOnce(
        new ApiClientError({
          status: 503,
          code: "AI_CANDIDATE_COMPARE_UNAVAILABLE",
          message: "AI candidate comparison is temporarily unavailable."
        })
      )
      .mockResolvedValueOnce(sampleResponse());

    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));

    expect(
      await screen.findByText("AI comparison is temporarily unavailable.")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/deterministic comparison above remains valid/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByText(/Candidate A covers more required skills/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText(/Candidate A covers more required skills/)).toBeInTheDocument();
    expect(postVacancyAiCompare).toHaveBeenCalledTimes(2);
  });

  it("keeps previous success visible when a later retry fails", async () => {
    postVacancyAiCompare
      .mockResolvedValueOnce(sampleResponse({ summary: "First successful summary." }))
      .mockRejectedValueOnce(
        new ApiClientError({
          status: 503,
          code: "AI_CANDIDATE_COMPARE_UNAVAILABLE",
          message: "AI candidate comparison is temporarily unavailable."
        })
      );

    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(await screen.findByText("First successful summary.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(
      await screen.findByText("AI comparison is temporarily unavailable.")
    ).toBeInTheDocument();
    expect(screen.getByText("First successful summary.")).toBeInTheDocument();
  });

  it("disables generate action for invalid selection size", () => {
    renderSection({ candidateIds: ["candidate-1"], enabled: true });
    expect(screen.getByRole("button", { name: "Generate AI comparison" })).toBeDisabled();
    expect(postVacancyAiCompare).not.toHaveBeenCalled();
  });
});

describe("CandidateComparisonView with AI panel", () => {
  beforeEach(() => {
    postVacancyAiCompare.mockReset();
    shortlistQuery.mockReturnValue({
      data: {
        entries: [entry("candidate-1"), entry("candidate-2")]
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn()
    });
    matchesQuery.mockReturnValue({
      data: { matches },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn()
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("keeps the deterministic comparison table intact after AI error", async () => {
    postVacancyAiCompare.mockRejectedValue(
      new ApiClientError({
        status: 503,
        code: "AI_CANDIDATE_COMPARE_UNAVAILABLE",
        message: "AI candidate comparison is temporarily unavailable."
      })
    );

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
    });
    render(
      <QueryClientProvider client={client}>
        <CandidateComparisonView
          vacancyId="vacancy-1"
          selectedCandidateIds={["candidate-1", "candidate-2"]}
          enabled
        />
      </QueryClientProvider>
    );

    expect(screen.getByRole("region", { name: "Candidate comparison table" })).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("74%")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Generate AI comparison" }));
    expect(
      await screen.findByText("AI comparison is temporarily unavailable.")
    ).toBeInTheDocument();

    expect(screen.getByRole("region", { name: "Candidate comparison table" })).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("74%")).toBeInTheDocument();
    expect(screen.getAllByText("TypeScript").length).toBeGreaterThan(0);
  });

  it("does not auto-call AI on compare page load", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
    });
    render(
      <QueryClientProvider client={client}>
        <CandidateComparisonView
          vacancyId="vacancy-1"
          selectedCandidateIds={["candidate-1", "candidate-2"]}
          enabled
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Generate AI comparison" })).toBeInTheDocument();
    });
    expect(postVacancyAiCompare).not.toHaveBeenCalled();
  });
});

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { InterviewQuestionsWorkspace } from "@/features/match-details/interview-questions-workspace";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { ApiClientError } from "@/lib/api/error";
import type { InterviewQuestionsResponse } from "@/lib/api/types/interview-questions";

const apiMocks = vi.hoisted(() => ({
  getInterviewQuestions: vi.fn(),
  refreshInterviewQuestions: vi.fn()
}));

const employerHooks = vi.hoisted(() => ({
  matchDetailsQuery: vi.fn()
}));

vi.mock("@/lib/api/interview-questions", () => ({
  getInterviewQuestions: (...args: unknown[]) => apiMocks.getInterviewQuestions(...args),
  refreshInterviewQuestions: (...args: unknown[]) => apiMocks.refreshInterviewQuestions(...args)
}));

vi.mock("@/lib/employer/hooks", () => ({
  useMatchDetailsQuery: () => employerHooks.matchDetailsQuery()
}));

const details = {
  candidate: {
    id: "candidate-1",
    name: "Alex Morgan",
    headline: "Backend Engineer",
    avatar: null
  },
  match: {
    score: 82,
    required: { matched: ["Python"], missing: ["Redis"] },
    preferred: { matched: [], missing: [] }
  },
  passport: { top_skills: [], skills: [] },
  evidence: [],
  roadmap: []
};

const questions: InterviewQuestionsResponse = {
  questions: [
    {
      category: "technical",
      question: "How have you used Python in production systems?",
      reason: "Python is a matched required skill.",
      target_skill: "Python",
      evidence_basis: "Sources: github_repository"
    },
    {
      category: "risk_validation",
      question: "How would you ramp up on Redis for this role?",
      reason: "Redis is missing from confirmed evidence.",
      target_skill: "Redis",
      evidence_basis: null
    },
    {
      category: "ownership",
      question: "What delivery decision did you personally own recently?",
      reason: "Ownership should be validated with observable outcomes.",
      target_skill: null,
      evidence_basis: null
    }
  ]
};

function renderWorkspace(
  options: Readonly<{ candidateId?: string; vacancyId?: string }> = {}
) {
  const candidateId = options.candidateId ?? "candidate-1";
  const vacancyId = options.vacancyId ?? "vacancy-1";
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <InterviewQuestionsWorkspace candidateId={candidateId} vacancyId={vacancyId} enabled />
    </QueryClientProvider>
  );
  return { ...view, queryClient, candidateId, vacancyId };
}

beforeEach(() => {
  employerHooks.matchDetailsQuery.mockReturnValue({
    data: details,
    isLoading: false,
    isError: false
  });
  apiMocks.getInterviewQuestions.mockResolvedValue(questions);
  apiMocks.refreshInterviewQuestions.mockResolvedValue({
    questions: [
      {
        category: "experience",
        question: "Walk through a recent backend delivery you owned.",
        reason: "Regenerated experience probe.",
        target_skill: null,
        evidence_basis: null
      }
    ]
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("InterviewQuestionsWorkspace", () => {
  it("loads the canonical query and renders grouped human-readable categories", async () => {
    renderWorkspace();

    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();
    expect(apiMocks.getInterviewQuestions).toHaveBeenCalledWith("candidate-1", "vacancy-1");
    expect(screen.getByRole("heading", { name: "Technical" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Risk validation" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ownership" })).toBeInTheDocument();
    expect(screen.queryByText("risk_validation")).not.toBeInTheDocument();
    expect(screen.getAllByText("Why this matters").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Target skill").length).toBeGreaterThan(0);
    expect(screen.getByText("Python", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Gap")).toBeInTheDocument();
    expect(screen.getByText("Questions prepared").parentElement).toHaveTextContent("3");
    expect(screen.getByText("Required matched").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Required missing").parentElement).toHaveTextContent("1");
    expect(
      screen.getByText(/AI-generated interview suggestions\. Review each question/)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Interview Scorecard" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/scorecard?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "Questions" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByLabelText(/technical competency/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("renders target skill and evidence labels only when present", async () => {
    apiMocks.getInterviewQuestions.mockResolvedValue({
      questions: [
        {
          category: "ownership",
          question: "What delivery decision did you personally own recently?",
          reason: "Ownership should be validated with observable outcomes.",
          target_skill: null,
          evidence_basis: null
        },
        {
          category: "experience",
          question: "Describe a recent backend delivery you owned.",
          reason: "Experience probe for delivery ownership.",
          target_skill: null,
          evidence_basis: "Sources: github_repository"
        }
      ]
    });
    renderWorkspace();

    expect(
      await screen.findByText("What delivery decision did you personally own recently?")
    ).toBeInTheDocument();
    expect(screen.queryByText("Target skill")).not.toBeInTheDocument();
    expect(screen.queryByText("Gap")).not.toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Sources: github_repository")).toBeInTheDocument();
  });

  it("shows loading state while the canonical query is pending", () => {
    apiMocks.getInterviewQuestions.mockReturnValue(new Promise(() => undefined));
    renderWorkspace();
    expect(screen.getByLabelText("Loading interview questions")).toBeInTheDocument();
  });

  it("shows a safe provider error and retries with the normal request", async () => {
    apiMocks.getInterviewQuestions.mockRejectedValue(
      new ApiClientError({
        status: 503,
        code: "INTERVIEW_QUESTIONS_UNAVAILABLE",
        message: "hidden details"
      })
    );
    renderWorkspace();

    expect(
      await screen.findByText("Interview questions are temporarily unavailable.")
    ).toBeInTheDocument();
    expect(screen.queryByText("hidden details")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Regenerate" })).toBeDisabled();

    apiMocks.getInterviewQuestions.mockResolvedValue(questions);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();
    expect(apiMocks.refreshInterviewQuestions).not.toHaveBeenCalled();
  });

  it("regenerates with refresh=true, disables the button, and updates canonical data", async () => {
    renderWorkspace();
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();

    let resolveRefresh: (value: InterviewQuestionsResponse) => void = () => undefined;
    apiMocks.refreshInterviewQuestions.mockReturnValue(
      new Promise((resolve) => {
        resolveRefresh = resolve;
      })
    );

    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Regenerating..." })).toBeDisabled();
    });
    expect(screen.getByText("How have you used Python in production systems?")).toBeInTheDocument();

    resolveRefresh({
      questions: [
        {
          category: "experience",
          question: "Walk through a recent backend delivery you owned.",
          reason: "Regenerated experience probe.",
          target_skill: null,
          evidence_basis: null
        }
      ]
    });

    expect(
      await screen.findByText("Walk through a recent backend delivery you owned.")
    ).toBeInTheDocument();
    expect(apiMocks.refreshInterviewQuestions).toHaveBeenCalledWith("candidate-1", "vacancy-1");
    expect(
      screen.queryByText("How have you used Python in production systems?")
    ).not.toBeInTheDocument();
  });

  it("keeps previously visible questions when regenerate fails", async () => {
    renderWorkspace();
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();

    apiMocks.refreshInterviewQuestions.mockRejectedValue(
      new ApiClientError({
        status: 503,
        code: "INTERVIEW_QUESTIONS_UNAVAILABLE",
        message: "fail"
      })
    );
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));

    expect(await screen.findByText(/Could not regenerate interview questions/)).toBeInTheDocument();
    expect(screen.getByText("How have you used Python in production systems?")).toBeInTheDocument();
  });

  it("does not show previous candidate questions after identity change", async () => {
    const { rerender, queryClient } = renderWorkspace();
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();

    apiMocks.getInterviewQuestions.mockResolvedValue({
      questions: [
        {
          category: "technical",
          question: "How have you applied Kafka in event pipelines?",
          reason: "Different candidate context.",
          target_skill: "Kafka",
          evidence_basis: null
        }
      ]
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <InterviewQuestionsWorkspace candidateId="candidate-2" vacancyId="vacancy-1" enabled />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("How have you applied Kafka in event pipelines?")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("How have you used Python in production systems?")
    ).not.toBeInTheDocument();
  });

  it("does not show previous vacancy questions after vacancy identity change", async () => {
    const { rerender, queryClient } = renderWorkspace();
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();

    apiMocks.getInterviewQuestions.mockResolvedValue({
      questions: [
        {
          category: "experience",
          question: "Describe your work with GraphQL APIs.",
          reason: "Different vacancy context.",
          target_skill: "GraphQL",
          evidence_basis: null
        }
      ]
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <InterviewQuestionsWorkspace candidateId="candidate-1" vacancyId="vacancy-2" enabled />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Describe your work with GraphQL APIs.")).toBeInTheDocument();
    expect(
      screen.queryByText("How have you used Python in production systems?")
    ).not.toBeInTheDocument();
  });

  it("clears regenerate error state when candidate identity changes", async () => {
    const { rerender, queryClient } = renderWorkspace();
    expect(
      await screen.findByText("How have you used Python in production systems?")
    ).toBeInTheDocument();

    apiMocks.refreshInterviewQuestions.mockRejectedValue(
      new ApiClientError({
        status: 503,
        code: "INTERVIEW_QUESTIONS_UNAVAILABLE",
        message: "fail"
      })
    );
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    expect(await screen.findByText(/Could not regenerate interview questions/)).toBeInTheDocument();

    apiMocks.getInterviewQuestions.mockResolvedValue({
      questions: [
        {
          category: "technical",
          question: "How have you applied Kafka in event pipelines?",
          reason: "Different candidate context.",
          target_skill: "Kafka",
          evidence_basis: null
        }
      ]
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <InterviewQuestionsWorkspace candidateId="candidate-2" vacancyId="vacancy-1" enabled />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("How have you applied Kafka in event pipelines?")
    ).toBeInTheDocument();
    expect(screen.queryByText(/Could not regenerate interview questions/)).not.toBeInTheDocument();
  });
});

describe("MatchReviewNavigation questions tab", () => {
  it("preserves vacancy_id across all tabs and marks Questions active", () => {
    render(
      <MatchReviewNavigation candidateId="candidate-1" vacancyId="vacancy-9" active="questions" />
    );

    expect(screen.getByRole("link", { name: "Candidate Review" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1?vacancy_id=vacancy-9"
    );
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/ai-hiring?vacancy_id=vacancy-9"
    );
    expect(screen.getByRole("link", { name: "Questions" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/interview-questions?vacancy_id=vacancy-9"
    );
    expect(screen.getByRole("link", { name: "Interview Scorecard" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/scorecard?vacancy_id=vacancy-9"
    );
    expect(screen.getByRole("link", { name: "Questions" })).toHaveAttribute("aria-current", "page");
  });
});

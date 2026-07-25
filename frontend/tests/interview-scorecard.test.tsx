import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { VacancyShortlistView } from "@/features/employer/vacancy-shortlist-view";
import { EmployerInterviewScorecardWorkspace } from "@/features/match-details/interview-scorecard-workspace";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { ApiClientError } from "@/lib/api/error";
import type { InterviewScorecard } from "@/lib/api/types/interview-scorecard";
import type { EmployerShortlistEntry, VacancyMatch } from "@/lib/api/types/employer";

const apiMocks = vi.hoisted(() => ({
  getInterviewScorecard: vi.fn(),
  putInterviewScorecard: vi.fn()
}));

const employerHooks = vi.hoisted(() => ({
  matchDetailsQuery: vi.fn(),
  shortlistQuery: vi.fn(),
  matchesQuery: vi.fn(),
  vacancyDetailQuery: vi.fn(),
  removeState: vi.fn(),
  updateStageState: vi.fn(),
  updateNoteState: vi.fn()
}));

vi.mock("@/lib/api/interview-scorecard", () => ({
  getInterviewScorecard: (...args: unknown[]) => apiMocks.getInterviewScorecard(...args),
  putInterviewScorecard: (...args: unknown[]) => apiMocks.putInterviewScorecard(...args)
}));

vi.mock("@/lib/employer/hooks", () => ({
  useMatchDetailsQuery: () => employerHooks.matchDetailsQuery(),
  useEmployerVacancyQuery: () => employerHooks.vacancyDetailQuery(),
  useVacancyMatchesQuery: () => employerHooks.matchesQuery(),
  useVacancyShortlistQuery: () => employerHooks.shortlistQuery(),
  useRemoveCandidateFromShortlist: () => employerHooks.removeState(),
  useUpdateEmployerShortlistStage: () => employerHooks.updateStageState(),
  useUpdateEmployerShortlistNote: () => employerHooks.updateNoteState()
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
    required: { matched: ["Python"], missing: [] },
    preferred: { matched: [], missing: [] }
  },
  passport: { top_skills: [], skills: [] },
  evidence: [],
  roadmap: []
};

const scorecard: InterviewScorecard = {
  id: "scorecard-1",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-1",
  technical_competency: 4,
  experience_relevance: 3,
  communication: 5,
  ownership: 4,
  interview_summary: "Solid depth",
  interview_notes: "Discussed systems design",
  recommendation: "yes",
  created_at: "2026-07-25T10:00:00Z",
  updated_at: "2026-07-25T10:00:00Z"
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
      <EmployerInterviewScorecardWorkspace
        candidateId={candidateId}
        vacancyId={vacancyId}
        enabled
      />
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
  employerHooks.vacancyDetailQuery.mockReturnValue({
    data: {
      id: "vacancy-1",
      title: "Backend Engineer",
      description: null,
      status: "open",
      created_at: "2026-07-20T10:00:00Z"
    },
    isLoading: false,
    isError: false
  });
  employerHooks.matchesQuery.mockReturnValue({
    data: {
      matches: [
        {
          candidate_id: "candidate-1",
          candidate_name: "Alex Morgan",
          score: 82,
          required: { matched: ["Python"], missing: [] },
          preferred: { matched: [], missing: [] }
        } satisfies VacancyMatch
      ]
    },
    isLoading: false,
    isError: false
  });
  employerHooks.removeState.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    reset: vi.fn()
  });
  employerHooks.updateStageState.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    variables: undefined,
    reset: vi.fn()
  });
  employerHooks.updateNoteState.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    variables: undefined,
    reset: vi.fn()
  });
  apiMocks.getInterviewScorecard.mockReset();
  apiMocks.putInterviewScorecard.mockReset();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("EmployerInterviewScorecardWorkspace", () => {
  it("shows empty editable form when scorecard is not found", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "SCORECARD_NOT_FOUND",
        message: "Interview scorecard not found"
      })
    );

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByLabelText("Technical Competency")).toHaveValue("");
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    expect(screen.getByText("Ownership / Accountability")).toBeInTheDocument();
    expect(screen.getByText("Interviewer Recommendation")).toBeInTheDocument();
    expect(screen.getByLabelText("Strong yes")).toBeInTheDocument();
    expect(screen.getByLabelText("Yes")).toBeInTheDocument();
    expect(screen.getByLabelText("Mixed")).toBeInTheDocument();
    expect(screen.getByLabelText("No")).toBeInTheDocument();
    expect(screen.queryByText("strong_yes")).not.toBeInTheDocument();
    expect(apiMocks.getInterviewScorecard).toHaveBeenCalledWith("vacancy-1", "candidate-1");
  });

  it("shows error state for unexpected GET failures without empty form", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 500,
        code: "DATABASE_ERROR",
        message: "Database operation failed"
      })
    );

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText("Interview scorecard unavailable")).toBeInTheDocument();
    expect(screen.queryByLabelText("Technical Competency")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("does not treat VACANCY_NOT_FOUND as an empty scorecard form", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "VACANCY_NOT_FOUND",
        message: "Vacancy not found"
      })
    );

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.queryByLabelText("Technical Competency")).not.toBeInTheDocument();
  });

  it("does not treat CANDIDATE_NOT_FOUND as an empty scorecard form", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "CANDIDATE_NOT_FOUND",
        message: "Candidate not found"
      })
    );

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText("Interview scorecard unavailable")).toBeInTheDocument();
    expect(screen.getByText("Candidate not found")).toBeInTheDocument();
    expect(screen.queryByLabelText("Technical Competency")).not.toBeInTheDocument();
  });

  it("preserves a dirty draft when the scorecard query refetches", async () => {
    apiMocks.getInterviewScorecard.mockResolvedValue(scorecard);

    const { queryClient } = renderWorkspace();

    await waitFor(() => {
      expect(screen.getByLabelText("Interview Summary")).toHaveValue("Solid depth");
    });

    fireEvent.change(screen.getByLabelText("Interview Summary"), {
      target: { value: "Draft that must survive refetch" }
    });
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();

    apiMocks.getInterviewScorecard.mockResolvedValue({
      ...scorecard,
      interview_summary: "Server value that must not wipe draft",
      updated_at: "2026-07-25T12:00:00Z"
    });
    await queryClient.refetchQueries({
      queryKey: ["employer", "vacancy", "vacancy-1", "scorecard", "candidate-1"]
    });

    await waitFor(() => {
      expect(apiMocks.getInterviewScorecard.mock.calls.length).toBeGreaterThan(1);
    });
    expect(screen.getByLabelText("Interview Summary")).toHaveValue(
      "Draft that must survive refetch"
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
  });

  it("resets the form when vacancy or candidate identity changes", async () => {
    apiMocks.getInterviewScorecard.mockImplementation(
      async (vacancyId: string, candidateId: string) => {
        if (candidateId === "candidate-2") {
          return {
            ...scorecard,
            id: "scorecard-2",
            vacancy_id: vacancyId,
            candidate_id: candidateId,
            interview_summary: "Second candidate summary",
            recommendation: "mixed" as const
          };
        }
        return scorecard;
      }
    );

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <EmployerInterviewScorecardWorkspace
          candidateId="candidate-1"
          vacancyId="vacancy-1"
          enabled
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Interview Summary")).toHaveValue("Solid depth");
    });
    fireEvent.change(screen.getByLabelText("Interview Summary"), {
      target: { value: "Unsaved draft for first candidate" }
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <EmployerInterviewScorecardWorkspace
          candidateId="candidate-2"
          vacancyId="vacancy-1"
          enabled
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Interview Summary")).toHaveValue("Second candidate summary");
    });
    expect(screen.getByLabelText("Mixed")).toBeChecked();
  });

  it("hydrates existing scorecard and saves exact PUT payload", async () => {
    apiMocks.getInterviewScorecard.mockResolvedValue(scorecard);
    apiMocks.putInterviewScorecard.mockResolvedValue({
      ...scorecard,
      technical_competency: 5,
      interview_summary: null,
      interview_notes: null,
      recommendation: "strong_yes",
      updated_at: "2026-07-25T11:00:00Z"
    });

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByLabelText("Technical Competency")).toHaveValue("4");
    });
    expect(screen.getByLabelText("Experience Relevance")).toHaveValue("3");
    expect(screen.getByLabelText("Communication")).toHaveValue("5");
    expect(screen.getByLabelText("Ownership / Accountability")).toHaveValue("4");
    expect(screen.getByLabelText("Interview Summary")).toHaveValue("Solid depth");
    expect(screen.getByLabelText("Interview Notes")).toHaveValue("Discussed systems design");
    expect(screen.getByLabelText("Yes")).toBeChecked();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Technical Competency"), {
      target: { value: "5" }
    });
    fireEvent.change(screen.getByLabelText("Interview Summary"), {
      target: { value: "   " }
    });
    fireEvent.change(screen.getByLabelText("Interview Notes"), {
      target: { value: "" }
    });
    fireEvent.click(screen.getByLabelText("Strong yes"));

    const saveButton = screen.getByRole("button", { name: "Save" });
    expect(saveButton).toBeEnabled();
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(apiMocks.putInterviewScorecard).toHaveBeenCalledTimes(1);
    });
    expect(apiMocks.putInterviewScorecard).toHaveBeenCalledWith("vacancy-1", "candidate-1", {
      technical_competency: 5,
      experience_relevance: 3,
      communication: 5,
      ownership: 4,
      interview_summary: null,
      interview_notes: null,
      recommendation: "strong_yes"
    });
    await waitFor(() => {
      expect(screen.getByText("Interview scorecard saved.")).toBeInTheDocument();
    });
    expect(apiMocks.putInterviewScorecard.mock.calls[0]?.[2]).not.toHaveProperty("stage");
  });

  it("does not autosave on field change and keeps values after PUT error", async () => {
    apiMocks.getInterviewScorecard.mockResolvedValue(scorecard);
    apiMocks.putInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 422,
        code: "VALIDATION_ERROR",
        message: "Validation failed"
      })
    );

    renderWorkspace();
    await waitFor(() => {
      expect(screen.getByLabelText("Technical Competency")).toHaveValue("4");
    });

    fireEvent.change(screen.getByLabelText("Interview Summary"), {
      target: { value: "Updated summary for retry" }
    });
    expect(apiMocks.putInterviewScorecard).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Validation failed");
    });
    expect(screen.getByLabelText("Interview Summary")).toHaveValue("Updated summary for retry");
  });

  it("disables Save while pending", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "SCORECARD_NOT_FOUND",
        message: "Interview scorecard not found"
      })
    );
    let resolvePut!: (value: InterviewScorecard) => void;
    apiMocks.putInterviewScorecard.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePut = resolve;
        })
    );

    renderWorkspace();
    await waitFor(() => {
      expect(screen.getByLabelText("Technical Competency")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Technical Competency"), { target: { value: "4" } });
    fireEvent.change(screen.getByLabelText("Experience Relevance"), { target: { value: "4" } });
    fireEvent.change(screen.getByLabelText("Communication"), { target: { value: "4" } });
    fireEvent.change(screen.getByLabelText("Ownership / Accountability"), {
      target: { value: "4" }
    });
    fireEvent.click(screen.getByLabelText("Yes"));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
    });
    expect(apiMocks.putInterviewScorecard).toHaveBeenCalledTimes(1);

    resolvePut({
      ...scorecard,
      recommendation: "yes"
    });
    await waitFor(() => {
      expect(screen.getByText("Interview scorecard saved.")).toBeInTheDocument();
    });
  });

  it("retries failed GET from the error state", async () => {
    apiMocks.getInterviewScorecard
      .mockRejectedValueOnce(
        new ApiClientError({
          status: 503,
          code: "UNAVAILABLE",
          message: "Temporarily unavailable"
        })
      )
      .mockRejectedValueOnce(
        new ApiClientError({
          status: 404,
          code: "SCORECARD_NOT_FOUND",
          message: "Interview scorecard not found"
        })
      );

    renderWorkspace();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => {
      expect(screen.getByLabelText("Technical Competency")).toBeInTheDocument();
    });
  });

  it("renders long summary and notes without breaking", async () => {
    apiMocks.getInterviewScorecard.mockResolvedValue({
      ...scorecard,
      interview_summary: "S".repeat(1200),
      interview_notes: "N".repeat(5000)
    });

    renderWorkspace();
    await waitFor(() => {
      expect(screen.getByLabelText("Interview Summary")).toHaveValue("S".repeat(1200));
    });
    expect(screen.getByLabelText("Interview Notes")).toHaveValue("N".repeat(5000));
  });

  it("does not show AI content or mutate shortlist/stage controls", async () => {
    apiMocks.getInterviewScorecard.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "SCORECARD_NOT_FOUND",
        message: "Interview scorecard not found"
      })
    );

    renderWorkspace();
    await waitFor(() => {
      expect(screen.getByText("Alex Morgan")).toBeInTheDocument();
    });

    expect(screen.queryByText(/AI-generated/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Hire")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Pipeline stage/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Private note/i)).not.toBeInTheDocument();
    expect(employerHooks.updateStageState().mutate).not.toHaveBeenCalled();
    expect(employerHooks.updateNoteState().mutate).not.toHaveBeenCalled();
  });
});

describe("MatchReviewNavigation scorecard tab", () => {
  it("includes Interview Scorecard and preserves vacancy_id with correct active states", () => {
    const { rerender } = render(
      <MatchReviewNavigation candidateId="candidate-1" vacancyId="vacancy-1" active="scorecard" />
    );

    expect(screen.getByRole("link", { name: "Interview Scorecard" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/scorecard?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "Interview Scorecard" })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("link", { name: "Candidate Review" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/ai-hiring?vacancy_id=vacancy-1"
    );
    expect(screen.getByRole("link", { name: "Questions" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/interview-questions?vacancy_id=vacancy-1"
    );

    rerender(
      <MatchReviewNavigation candidateId="candidate-1" vacancyId="vacancy-1" active="review" />
    );
    expect(screen.getByRole("link", { name: "Candidate Review" })).toHaveAttribute(
      "aria-current",
      "page"
    );

    rerender(<MatchReviewNavigation candidateId="candidate-1" vacancyId="vacancy-1" active="ai" />);
    expect(screen.getByRole("link", { name: "AI Hiring" })).toHaveAttribute("aria-current", "page");

    rerender(
      <MatchReviewNavigation candidateId="candidate-1" vacancyId="vacancy-1" active="questions" />
    );
    expect(screen.getByRole("link", { name: "Questions" })).toHaveAttribute("aria-current", "page");
  });
});

describe("Shortlist interview scorecard CTA", () => {
  it("shows CTA only for interview stage with correct href", () => {
    const interviewEntry: EmployerShortlistEntry = {
      id: "entry-1",
      vacancy_id: "vacancy-1",
      candidate_id: "candidate-1",
      stage: "interview",
      note: null,
      created_at: "2026-07-20T10:00:00Z",
      updated_at: "2026-07-20T10:00:00Z"
    };
    const screeningEntry: EmployerShortlistEntry = {
      ...interviewEntry,
      id: "entry-2",
      candidate_id: "candidate-2",
      stage: "screening"
    };

    employerHooks.shortlistQuery.mockReturnValue({
      data: { entries: [interviewEntry, screeningEntry] },
      isLoading: false,
      isError: false
    });
    employerHooks.matchesQuery.mockReturnValue({
      data: {
        matches: [
          {
            candidate_id: "candidate-1",
            candidate_name: "Alex Morgan",
            score: 82,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          },
          {
            candidate_id: "candidate-2",
            candidate_name: "Bea Chen",
            score: 70,
            required: { matched: [], missing: [] },
            preferred: { matched: [], missing: [] }
          }
        ]
      },
      isLoading: false,
      isError: false
    });

    render(
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
          })
        }
      >
        <VacancyShortlistView vacancyId="vacancy-1" enabled />
      </QueryClientProvider>
    );

    const scorecardLinks = screen.getAllByRole("link", { name: "Open interview scorecard" });
    expect(scorecardLinks).toHaveLength(1);
    expect(scorecardLinks[0]).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1/scorecard?vacancy_id=vacancy-1"
    );

    const beaCard = screen.getByText("Bea Chen").closest("li");
    expect(beaCard).not.toBeNull();
    expect(
      within(beaCard as HTMLElement).queryByRole("link", { name: "Open interview scorecard" })
    ).not.toBeInTheDocument();
  });
});

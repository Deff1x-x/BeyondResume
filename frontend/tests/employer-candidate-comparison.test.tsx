import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CandidateComparisonView,
  buildCompareHref,
  parseCompareCandidateIds
} from "@/features/employer/candidate-comparison-view";
import { VacancyShortlistView } from "@/features/employer/vacancy-shortlist-view";
import { ApiClientError } from "@/lib/api/error";
import type {
  EmployerShortlistEntry,
  VacancyMatch
} from "@/lib/api/types/employer";

vi.mock("@/features/employer/ai-candidate-compare-section", () => ({
  AiCandidateCompareSection: () => (
    <div data-testid="ai-candidate-compare-section-stub">AI Candidate Compare stub</div>
  )
}));

const hooksSpies = vi.hoisted(() => ({
  shortlistQuery: vi.fn(),
  matchesQuery: vi.fn(),
  vacancyDetailQuery: vi.fn(),
  matchDetailsQuery: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false
  })),
  matchExplanationQuery: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false
  })),
  removeMutate: vi.fn(),
  removeState: vi.fn(),
  updateStageMutate: vi.fn(),
  updateStageState: vi.fn(),
  updateNoteMutate: vi.fn(),
  updateNoteState: vi.fn()
}));

const {
  shortlistQuery,
  matchesQuery,
  vacancyDetailQuery,
  matchDetailsQuery,
  matchExplanationQuery,
  removeMutate,
  removeState,
  updateStageMutate,
  updateStageState,
  updateNoteMutate,
  updateNoteState
} = hooksSpies;

vi.mock("@/lib/employer/hooks", () => ({
  useAddVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerCompany: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useUpdateEmployerCompany: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn()
  }),
  useCreateEmployerVacancy: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useDeleteEmployerVacancy: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn()
  }),
  useDeleteVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useEmployerCompanyQuery: () => ({ data: null, isLoading: false, isError: false }),
  useEmployerSkillsQuery: () => ({
    data: [],
    isLoading: false,
    isError: false,
    isSuccess: true
  }),
  useEmployerVacanciesQuery: () => ({ data: [], isLoading: false, isError: false }),
  useEmployerVacancyQuery: () => vacancyDetailQuery(),
  useMatchDetailsQuery: () => matchDetailsQuery(),
  useMatchExplanationQuery: () => matchExplanationQuery(),
  useVacancyMatchesQuery: () => matchesQuery(),
  useVacancyRequirementsQuery: () => ({
    data: [],
    isLoading: false,
    isError: false,
    isSuccess: true
  }),
  useVacancyShortlistQuery: () => shortlistQuery(),
  useSaveCandidateToShortlist: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  }),
  useRemoveCandidateFromShortlist: () => removeState(),
  useUpdateEmployerShortlistStage: () => updateStageState(),
  useUpdateEmployerShortlistNote: () => updateNoteState(),
  vacancyMatchesQueryKey: (vacancyId: string) => ["employer", "vacancy", vacancyId, "matches"],
  vacancyShortlistQueryKey: (vacancyId: string) => [
    "employer",
    "vacancy",
    vacancyId,
    "shortlist"
  ]
}));

const vacancy = {
  id: "vacancy-1",
  title: "Frontend Engineer",
  description: "Build product UI",
  status: "open" as const,
  created_at: "2026-07-20T10:00:00Z"
};

const matches: VacancyMatch[] = [
  {
    candidate_id: "candidate-1",
    candidate_name: "Alex Morgan",
    score: 82,
    required: { matched: ["React"], missing: ["TypeScript"] },
    preferred: { matched: ["CSS"], missing: ["Jest"] }
  },
  {
    candidate_id: "candidate-2",
    candidate_name: "Bea Chen",
    score: 74,
    required: { matched: ["React"], missing: [] },
    preferred: { matched: ["Jest"], missing: ["GraphQL"] }
  },
  {
    candidate_id: "candidate-3",
    candidate_name: "Chris Diaz",
    score: 68,
    required: { matched: [], missing: ["React"] },
    preferred: { matched: [], missing: [] }
  },
  {
    candidate_id: "candidate-4",
    candidate_name: "Dana Lee",
    score: 61,
    required: { matched: ["React"], missing: ["Node"] },
    preferred: { matched: ["Docker"], missing: [] }
  },
  {
    candidate_id: "candidate-5",
    candidate_name: "Evan Park",
    score: 55,
    required: { matched: ["React"], missing: [] },
    preferred: { matched: [], missing: ["AWS"] }
  }
];

function entry(
  candidateId: string,
  overrides: Partial<EmployerShortlistEntry> = {}
): EmployerShortlistEntry {
  return {
    id: `entry-${candidateId}`,
    vacancy_id: "vacancy-1",
    candidate_id: candidateId,
    stage: "shortlisted",
    note: null,
    created_at: "2026-07-25T10:00:00Z",
    updated_at: "2026-07-25T10:00:00Z",
    ...overrides
  };
}

const fiveEntries = [
  entry("candidate-1", { note: "Strong frontend focus" }),
  entry("candidate-2", { stage: "interview" }),
  entry("candidate-3", { stage: "screening" }),
  entry("candidate-4"),
  entry("candidate-5", { stage: "offer" })
];

const loadError = new ApiClientError({
  status: 500,
  code: "DATABASE_ERROR",
  message: "Database operation failed",
  details: [],
  requestId: null
});

function readyQueries({
  shortlistEntries = fiveEntries.slice(0, 2),
  matchList = matches,
  shortlistLoading = false,
  matchesLoading = false,
  shortlistError = false,
  matchesError = false
}: {
  shortlistEntries?: EmployerShortlistEntry[];
  matchList?: VacancyMatch[];
  shortlistLoading?: boolean;
  matchesLoading?: boolean;
  shortlistError?: boolean;
  matchesError?: boolean;
} = {}) {
  vacancyDetailQuery.mockReturnValue({
    data: vacancy,
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  });
  shortlistQuery.mockReturnValue({
    data: shortlistError ? undefined : { entries: shortlistEntries },
    isLoading: shortlistLoading,
    isError: shortlistError,
    isSuccess: !shortlistLoading && !shortlistError,
    error: shortlistError ? loadError : null,
    refetch: vi.fn()
  });
  matchesQuery.mockReturnValue({
    data: matchesError ? undefined : { matches: matchList },
    isLoading: matchesLoading,
    isError: matchesError,
    isSuccess: !matchesLoading && !matchesError,
    error: matchesError ? loadError : null,
    refetch: vi.fn()
  });
}

beforeEach(() => {
  removeMutate.mockReset();
  updateStageMutate.mockReset();
  updateNoteMutate.mockReset();
  matchDetailsQuery.mockClear();
  matchExplanationQuery.mockClear();
  removeState.mockReturnValue({
    mutate: removeMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  });
  updateStageState.mockReturnValue({
    mutate: updateStageMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  });
  updateNoteState.mockReturnValue({
    mutate: updateNoteMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  });
  readyQueries();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("parseCompareCandidateIds / buildCompareHref", () => {
  it("deduplicates IDs while preserving first-seen order", () => {
    expect(parseCompareCandidateIds("candidate-2,candidate-1,candidate-2,candidate-1")).toEqual([
      "candidate-2",
      "candidate-1"
    ]);
  });

  it("trims empty segments and keeps UUID order", () => {
    expect(
      parseCompareCandidateIds(
        " 550e8400-e29b-41d4-a716-446655440000 , ,550e8400-e29b-41d4-a716-446655440001,"
      )
    ).toEqual([
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ]);
  });

  it("encodes reserved characters without double-encoding on parse roundtrip", () => {
    const href = buildCompareHref("vacancy 1", ["id/a", "id b"]);
    expect(href).toBe("/employer/vacancies/vacancy%201/compare?ids=id%2Fa,id%20b");
    const idsParam = new URL(href, "https://example.test").searchParams.get("ids");
    expect(parseCompareCandidateIds(idsParam)).toEqual(["id/a", "id b"]);
  });
});

describe("Shortlist comparison selection", () => {
  it("shows accessible checkboxes, empty selection, and disabled Compare CTA until two are selected", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    const alex = screen.getByRole("checkbox", {
      name: "Select Alex Morgan for comparison"
    });
    const bea = screen.getByRole("checkbox", {
      name: "Select Bea Chen for comparison"
    });
    expect(alex).not.toBeChecked();
    expect(bea).not.toBeChecked();
    expect(screen.getByText("0 selected")).toBeInTheDocument();

    const compareDisabled = screen.getByRole("button", {
      name: "Compare selected candidates"
    });
    expect(compareDisabled).toBeDisabled();
    fireEvent.click(compareDisabled);
    expect(screen.queryByRole("link", { name: "Compare selected candidates" })).not.toBeInTheDocument();

    fireEvent.click(alex);
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Compare selected candidates" })
    ).toBeDisabled();

    fireEvent.click(bea);
    expect(screen.getByText("2 selected")).toBeInTheDocument();
    const compareLink = screen.getByRole("link", {
      name: "Compare selected candidates"
    });
    expect(compareLink).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/compare?ids=candidate-1,candidate-2"
    );
  });

  it("caps selection at four, keeps selected boxes enabled, and preserves selection order in the URL", () => {
    readyQueries({ shortlistEntries: fiveEntries });
    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Bea Chen for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Chris Diaz for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Dana Lee for comparison" }));

    expect(screen.getByText("4 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: "Select Evan Park for comparison" })
    ).toBeDisabled();
    expect(
      screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" })
    ).not.toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    expect(screen.getByText("3 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: "Select Evan Park for comparison" })
    ).not.toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    expect(
      screen.getByRole("link", { name: "Compare selected candidates" })
    ).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/compare?ids=candidate-2,candidate-3,candidate-4,candidate-1"
    );
  });

  it("keeps hidden selected candidates when the stage filter changes", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Bea Chen for comparison" }));
    fireEvent.click(screen.getByRole("button", { name: "Interview" }));

    expect(
      screen.queryByRole("checkbox", { name: "Select Alex Morgan for comparison" })
    ).not.toBeInTheDocument();
    expect(screen.getByText("2 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Compare selected candidates" })
    ).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/compare?ids=candidate-1,candidate-2"
    );
  });

  it("preserves selection when stage or note values change for the same candidates", () => {
    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { stage: "shortlisted", note: "Old" }),
        entry("candidate-2", { stage: "interview", note: null })
      ]
    });
    const { rerender } = render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Bea Chen for comparison" }));

    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { stage: "offer", note: "New note" }),
        entry("candidate-2", { stage: "interview", note: "Also new" })
      ]
    });
    rerender(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("2 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Compare selected candidates" })
    ).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/compare?ids=candidate-1,candidate-2"
    );
    expect(
      screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" })
    ).toBeChecked();
  });

  it("removes a candidate from selection when Remove is clicked", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Bea Chen for comparison" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    );

    expect(removeMutate).toHaveBeenCalledWith("candidate-1");
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Compare selected candidates" })
    ).toBeDisabled();
  });

  it("clears stale selection when the server shortlist no longer includes a candidate", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    const { rerender } = render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Bea Chen for comparison" }));
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    readyQueries({ shortlistEntries: [entry("candidate-2", { stage: "interview" })] });
    rerender(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Compare selected candidates" })
    ).toBeDisabled();
  });

  it("keeps existing stage control and note editor working with selection present", () => {
    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { note: "Strong frontend focus" }),
        entry("candidate-2", { stage: "interview" })
      ]
    });
    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("checkbox", { name: "Select Alex Morgan for comparison" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" }), {
      target: { value: "offer" }
    });
    expect(updateStageMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      stage: "offer"
    });

    const note = screen.getByRole("textbox", { name: "Private note for Alex Morgan" });
    expect(note).toHaveValue("Strong frontend focus");
    fireEvent.change(note, { target: { value: "Updated note" } });
    fireEvent.click(screen.getByRole("button", { name: "Save note for Alex Morgan" }));
    expect(updateNoteMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      note: "Updated note"
    });
  });
});

describe("CandidateComparisonView", () => {
  it("renders two candidates in URL order with identity, score, skills, stage, note, and review links", () => {
    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { note: "Strong frontend focus" }),
        entry("candidate-2", { stage: "interview", note: null })
      ]
    });

    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-2", "candidate-1"]}
        enabled
      />
    );

    expect(screen.getByRole("heading", { name: "Candidate comparison" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Deterministic comparison" })
    ).toBeInTheDocument();
    const candidateHeadings = screen
      .getAllByRole("heading", { level: 2 })
      .map((node) => node.textContent)
      .filter((text) => text === "Bea Chen" || text === "Alex Morgan");
    expect(candidateHeadings).toEqual(["Bea Chen", "Alex Morgan"]);

    expect(screen.getByText("74%")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("Interview")).toBeInTheDocument();
    expect(screen.getByText("Shortlisted")).toBeInTheDocument();
    expect(screen.getByText("Strong frontend focus")).toBeInTheDocument();
    expect(screen.getByText("No private note")).toBeInTheDocument();
    expect(screen.getByText("TypeScript")).toBeInTheDocument();
    expect(screen.getByText("GraphQL")).toBeInTheDocument();
    expect(screen.getByText("CSS")).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Open Candidate Review for Bea Chen" })
    ).toHaveAttribute("href", "/employer/matches/candidate-2?vacancy_id=vacancy-1");
    expect(
      screen.getByRole("link", { name: "Open Candidate Review for Alex Morgan" })
    ).toHaveAttribute("href", "/employer/matches/candidate-1?vacancy_id=vacancy-1");

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /save note/i })).not.toBeInTheDocument();
  });

  it("renders score 0 instead of treating it as unavailable", () => {
    readyQueries({
      shortlistEntries: [entry("candidate-1"), entry("candidate-2")],
      matchList: [
        { ...matches[0], score: 0 },
        { ...matches[1], score: 74 }
      ]
    });

    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );

    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText("74%")).toBeInTheDocument();
  });

  it("lets invalid IDs fall through so four valid shortlist IDs still fill the cap", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 4) });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={[
          "invalid",
          "candidate-1",
          "candidate-2",
          "candidate-3",
          "candidate-4"
        ]}
        enabled
      />
    );

    const headings = screen
      .getAllByRole("heading", { level: 2 })
      .map((node) => node.textContent)
      .filter((text) => text !== "Deterministic comparison");
    expect(headings).toEqual(["Alex Morgan", "Bea Chen", "Chris Diaz", "Dana Lee"]);
    expect(
      screen.queryByText("Only the first four shortlisted candidates are shown.")
    ).not.toBeInTheDocument();
  });

  it("ignores invalid IDs, caps at four valid shortlist IDs, and preserves URL order", () => {
    readyQueries({ shortlistEntries: fiveEntries });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={[
          "candidate-5",
          "missing",
          "candidate-1",
          "candidate-5",
          "candidate-2",
          "candidate-3",
          "candidate-4"
        ]}
        enabled
      />
    );

    expect(screen.getByText("Only the first four shortlisted candidates are shown.")).toBeInTheDocument();
    const headings = screen
      .getAllByRole("heading", { level: 2 })
      .map((node) => node.textContent)
      .filter((text) => text !== "Deterministic comparison");
    expect(headings).toEqual(["Evan Park", "Alex Morgan", "Bea Chen", "Chris Diaz"]);
    expect(screen.queryByRole("heading", { name: "Dana Lee" })).not.toBeInTheDocument();
  });

  it("shows the empty state with a back link when fewer than two valid IDs remain", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["missing", "candidate-1"]}
        enabled
      />
    );

    expect(
      screen.getByText("Select at least two shortlisted candidates to compare.")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to shortlist" })).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/shortlist"
    );
  });

  it("shows loading without a premature empty state", () => {
    readyQueries({ shortlistLoading: true, matchesLoading: true });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1"]}
        enabled
      />
    );

    expect(screen.getByRole("status", { name: "Loading candidate comparison" })).toBeInTheDocument();
    expect(
      screen.queryByText("Select at least two shortlisted candidates to compare.")
    ).not.toBeInTheDocument();
  });

  it("shows matches loading without a premature empty state", () => {
    readyQueries({ matchesLoading: true });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1"]}
        enabled
      />
    );

    expect(screen.getByRole("status", { name: "Loading candidate comparison" })).toBeInTheDocument();
    expect(
      screen.queryByText("Select at least two shortlisted candidates to compare.")
    ).not.toBeInTheDocument();
  });

  it("shows shortlist and matches errors at page level", () => {
    readyQueries({ shortlistError: true });
    const { rerender } = render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    expect(screen.queryByText("Unavailable")).not.toBeInTheDocument();

    readyQueries({ matchesError: true });
    rerender(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    expect(screen.queryByText("0%")).not.toBeInTheDocument();
  });

  it("keeps the page usable when match data is missing for a shortlisted candidate", () => {
    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { stage: "screening", note: "Known hire track" }),
        entry("candidate-unmatched", { stage: "interview" })
      ],
      matchList: matches.slice(0, 1)
    });

    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-unmatched"]}
        enabled
      />
    );

    expect(screen.getByRole("heading", { name: "Alex Morgan" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "candidate-unmatched" })).toBeInTheDocument();
    expect(screen.getByText("Screening")).toBeInTheDocument();
    expect(screen.getByText("Interview")).toBeInTheDocument();
    expect(screen.getByText("Known hire track")).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("renders the full private note without truncation", () => {
    const longNote = `${"Long note line\n".repeat(40)}Tail marker ${"x".repeat(40)}`;
    readyQueries({
      shortlistEntries: [
        entry("candidate-1", { note: longNote }),
        entry("candidate-2", { stage: "interview" })
      ]
    });

    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );

    expect(
      screen.getByText((_, node) => node?.tagName === "P" && node.textContent === longNote)
    ).toBeInTheDocument();
    expect(screen.queryByText(/Note preview truncated/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Tail marker x{40}/)).toBeInTheDocument();
  });

  it("exposes an accessible comparison region and candidate headings", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );

    expect(
      screen.getByRole("region", { name: "Candidate comparison table" })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Candidate comparison" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Alex Morgan" })).toBeInTheDocument();
  });

  it("does not invoke match-details or legacy AI explanation hooks", () => {
    readyQueries({ shortlistEntries: fiveEntries.slice(0, 2) });
    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-1", "candidate-2"]}
        enabled
      />
    );

    expect(shortlistQuery).toHaveBeenCalled();
    expect(matchesQuery).toHaveBeenCalled();
    expect(matchDetailsQuery).not.toHaveBeenCalled();
    expect(matchExplanationQuery).not.toHaveBeenCalled();
    expect(screen.getByTestId("ai-candidate-compare-section-stub")).toBeInTheDocument();
    expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
  });
});

describe("Candidate comparison QueryClient cache reactivity", () => {
  it("updates stage, note, score, and removal from the shared production query cache", async () => {
    vi.resetModules();
    vi.doUnmock("@/lib/employer/hooks");

    const hooks = await import("@/lib/employer/hooks");
    const { CandidateComparisonView: LiveComparisonView } = await import(
      "@/features/employer/candidate-comparison-view"
    );

    const fetchMock = vi.fn(() =>
      Promise.reject(new Error("unexpected network request during cache test"))
    );
    vi.stubGlobal("fetch", fetchMock);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [
        entry("candidate-1", { stage: "shortlisted", note: "Original note" }),
        entry("candidate-2", { stage: "interview", note: null })
      ]
    });
    queryClient.setQueryData(hooks.vacancyMatchesQueryKey("vacancy-1"), {
      matches: [
        { ...matches[0], score: 82 },
        { ...matches[1], score: 74 }
      ]
    });

    render(
      <QueryClientProvider client={queryClient}>
        <LiveComparisonView
          vacancyId="vacancy-1"
          selectedCandidateIds={["candidate-1", "candidate-2"]}
          enabled
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("Shortlisted")).toBeInTheDocument();
    expect(screen.getByText("Original note")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [
        entry("candidate-1", { stage: "offer", note: "Updated note" }),
        entry("candidate-2", { stage: "interview", note: null })
      ]
    });
    queryClient.setQueryData(hooks.vacancyMatchesQueryKey("vacancy-1"), {
      matches: [
        { ...matches[0], score: 91 },
        { ...matches[1], score: 74 }
      ]
    });

    await waitFor(() => {
      expect(screen.getByText("Offer")).toBeInTheDocument();
      expect(screen.getByText("Updated note")).toBeInTheDocument();
      expect(screen.getByText("91%")).toBeInTheDocument();
    });

    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [entry("candidate-2", { stage: "interview", note: null })]
    });

    await waitFor(() => {
      expect(
        screen.getByText("Select at least two shortlisted candidates to compare.")
      ).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: "Alex Morgan" })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("Skill list empty placeholders on comparison", () => {
  it("shows None for empty skill groups", () => {
    readyQueries({
      shortlistEntries: [
        entry("candidate-2", { stage: "interview" }),
        entry("candidate-3", { stage: "screening" })
      ]
    });

    render(
      <CandidateComparisonView
        vacancyId="vacancy-1"
        selectedCandidateIds={["candidate-2", "candidate-3"]}
        enabled
      />
    );

    const region = screen.getByRole("region", { name: "Candidate comparison table" });
    expect(within(region).getAllByText("None").length).toBeGreaterThanOrEqual(1);
  });
});

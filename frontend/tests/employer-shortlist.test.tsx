import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ShortlistSaveButton } from "@/features/employer/shortlist-save-button";
import { VacancyShortlistView } from "@/features/employer/vacancy-shortlist-view";
import { EmployerSection } from "@/features/employer-section";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import {
  listVacancyShortlist,
  removeCandidateFromShortlist,
  saveCandidateToShortlist
} from "@/lib/api/employer";
import { ApiClientError } from "@/lib/api/error";

const shortlistQuery = vi.fn();
const saveMutate = vi.fn();
const removeMutate = vi.fn();
const saveState = vi.fn();
const removeState = vi.fn();
const matchDetailsQuery = vi.fn();
const companyQuery = vi.fn();
const vacanciesQuery = vi.fn();
const vacancyDetailQuery = vi.fn();
const requirementsQuery = vi.fn();
const matchesQuery = vi.fn();
const dashboardRequirements = vi.fn();
const dashboardMatches = vi.fn();

vi.mock("@tanstack/react-query", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-query")>()),
  useQueries: ({ queries }: { queries: Array<{ queryKey: readonly string[] }> }) =>
    queries.map((query) =>
      query.queryKey.at(-1) === "requirements"
        ? dashboardRequirements(query.queryKey)
        : dashboardMatches(query.queryKey)
    )
}));

vi.mock("@/lib/employer/hooks", () => ({
  useAddVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerCompany: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerVacancy: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useDeleteVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useEmployerCompanyQuery: () => companyQuery(),
  useEmployerSkillsQuery: () => ({
    data: [],
    isLoading: false,
    isError: false,
    isSuccess: true
  }),
  useEmployerVacanciesQuery: () => vacanciesQuery(),
  useEmployerVacancyQuery: () => vacancyDetailQuery(),
  useMatchDetailsQuery: () => matchDetailsQuery(),
  useVacancyMatchesQuery: () => matchesQuery(),
  useVacancyRequirementsQuery: () => requirementsQuery(),
  useVacancyShortlistQuery: () => shortlistQuery(),
  useSaveCandidateToShortlist: () => saveState(),
  useRemoveCandidateFromShortlist: () => removeState(),
  vacancyMatchesQueryKey: (vacancyId: string) => ["employer", "vacancy", vacancyId, "matches"],
  vacancyRequirementsQueryKey: (vacancyId: string) => [
    "employer",
    "vacancy",
    vacancyId,
    "requirements"
  ],
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

const orderedMatches = [
  {
    candidate_id: "candidate-1",
    candidate_name: "Alex Morgan",
    score: 82,
    required: { matched: ["React"], missing: [] },
    preferred: { matched: [], missing: ["Jest"] }
  },
  {
    candidate_id: "candidate-2",
    candidate_name: "Bea Chen",
    score: 74,
    required: { matched: ["React"], missing: [] },
    preferred: { matched: ["Jest"], missing: [] }
  }
];

const matchDetails = {
  candidate: {
    id: "candidate-1",
    name: "Alex Morgan",
    headline: "Frontend Engineer",
    avatar: null
  },
  match: {
    score: 82,
    required: { matched: ["React"], missing: [] },
    preferred: { matched: [], missing: ["Jest"] }
  },
  passport: { top_skills: ["React"], skills: [] },
  evidence: [],
  roadmap: []
};

const shortlistEntry = {
  id: "entry-1",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-1",
  created_at: "2026-07-25T10:00:00Z",
  updated_at: "2026-07-25T10:00:00Z"
};

const secondShortlistEntry = {
  id: "entry-2",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-2",
  created_at: "2026-07-25T11:00:00Z",
  updated_at: "2026-07-25T11:00:00Z"
};

const shortlistLoadError = new ApiClientError({
  status: 500,
  code: "DATABASE_ERROR",
  message: "Database operation failed",
  details: [],
  requestId: null
});

function readyEmployerWorkspace({
  shortlistEntries = [] as typeof shortlistEntry[]
} = {}) {
  companyQuery.mockReturnValue({
    data: { company_name: "Beyond", website: null, description: null },
    isLoading: false,
    isError: false
  });
  vacanciesQuery.mockReturnValue({
    data: [vacancy],
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  });
  vacancyDetailQuery.mockReturnValue({ data: vacancy, isLoading: false, isError: false });
  requirementsQuery.mockReturnValue({
    data: [],
    isLoading: false,
    isError: false,
    isSuccess: true
  });
  matchesQuery.mockReturnValue({
    data: { matches: orderedMatches },
    isLoading: false,
    isError: false,
    isSuccess: true,
    refetch: vi.fn()
  });
  shortlistQuery.mockReturnValue({
    data: { entries: shortlistEntries },
    isLoading: false,
    isError: false,
    isSuccess: true,
    refetch: vi.fn()
  });
  dashboardRequirements.mockReturnValue({ data: [] });
  dashboardMatches.mockReturnValue({ data: { matches: orderedMatches } });
}

beforeEach(() => {
  saveMutate.mockReset();
  removeMutate.mockReset();
  saveState.mockReturnValue({
    mutate: saveMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  });
  removeState.mockReturnValue({
    mutate: removeMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
    reset: vi.fn()
  });
  shortlistQuery.mockReturnValue({
    data: { entries: [] },
    isLoading: false,
    isError: false,
    isSuccess: true,
    refetch: vi.fn()
  });
  matchDetailsQuery.mockReturnValue({
    data: matchDetails,
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  });
  vacancyDetailQuery.mockReturnValue({ data: vacancy, isLoading: false, isError: false });
  matchesQuery.mockReturnValue({
    data: { matches: orderedMatches },
    isLoading: false,
    isError: false,
    isSuccess: true,
    refetch: vi.fn()
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Employer shortlist UI", () => {
  it("saves a candidate from Candidate Review via PUT", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });

    render(
      <ShortlistSaveButton
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        candidateName="Alex Morgan"
      />
    );

    const saveButton = screen.getByRole("button", { name: "Save Alex Morgan to shortlist" });
    expect(saveButton).toHaveTextContent("Save");
    fireEvent.click(saveButton);
    expect(saveMutate).toHaveBeenCalledWith("candidate-1");
    expect(removeMutate).not.toHaveBeenCalled();
  });

  it("removes a saved candidate from Candidate Review via DELETE", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });

    render(
      <ShortlistSaveButton
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        candidateName="Alex Morgan"
      />
    );

    const savedButton = screen.getByRole("button", {
      name: "Remove Alex Morgan from shortlist"
    });
    expect(savedButton).toHaveTextContent("Saved");
    fireEvent.click(savedButton);
    expect(removeMutate).toHaveBeenCalledWith("candidate-1");
    expect(saveMutate).not.toHaveBeenCalled();
  });

  it("disables the save control while a request is pending", () => {
    saveState.mockReturnValue({
      mutate: saveMutate,
      isPending: true,
      isError: false,
      error: null,
      variables: "candidate-1",
      reset: vi.fn()
    });

    render(
      <ShortlistSaveButton
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        candidateName="Alex Morgan"
      />
    );

    const button = screen.getByRole("button", { name: "Save Alex Morgan to shortlist" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    fireEvent.click(button);
    expect(saveMutate).not.toHaveBeenCalled();
  });

  it("shows an inline shortlist error without inventing a toast framework", () => {
    saveState.mockReturnValue({
      mutate: saveMutate,
      isPending: false,
      isError: true,
      error: new ApiClientError({
        status: 500,
        code: "DATABASE_ERROR",
        message: "Database operation failed",
        details: [],
        requestId: null
      }),
      variables: undefined,
      reset: vi.fn()
    });

    render(
      <ShortlistSaveButton vacancyId="vacancy-1" candidateId="candidate-1" />
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
  });

  it("shows Saved badge in Candidate Review when the backend shortlist includes the candidate", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });

    render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.getAllByText("Saved").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    ).toBeInTheDocument();
    expect(screen.queryByText("employer_id")).not.toBeInTheDocument();
  });

  it("filters Candidate matches by All and Saved without changing match order", () => {
    readyEmployerWorkspace({ shortlistEntries: [shortlistEntry] });
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    expect(screen.getByRole("link", { name: "Open shortlist" })).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/shortlist"
    );
    expect(screen.getAllByText("Saved").length).toBeGreaterThan(0);

    const linksAll = screen
      .getAllByRole("link", { name: /Review candidate/ })
      .map((link) => link.getAttribute("href"));
    expect(linksAll).toEqual([
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-2?vacancy_id=vacancy-1"
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Saved" }));
    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Review candidate Bea Chen" })
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getByRole("link", { name: "Review candidate Bea Chen" })).toBeInTheDocument();
  });

  it("keeps the existing match score order under the Saved filter regardless of shortlist order", () => {
    readyEmployerWorkspace({
      shortlistEntries: [secondShortlistEntry, shortlistEntry]
    });
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));
    fireEvent.click(screen.getByRole("button", { name: "Saved" }));

    const savedLinks = screen
      .getAllByRole("link", { name: /Review candidate/ })
      .map((link) => link.getAttribute("href"));
    expect(savedLinks).toEqual([
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-2?vacancy_id=vacancy-1"
    ]);
  });

  it("surfaces a shortlist load error in the vacancy workspace instead of an empty Saved state", () => {
    readyEmployerWorkspace();
    shortlistQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      isSuccess: false,
      error: shortlistLoadError,
      refetch: vi.fn()
    });
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));
    fireEvent.click(screen.getByRole("button", { name: "Saved" }));

    expect(screen.getAllByRole("alert").some((alert) =>
      alert.textContent?.includes("Database operation failed")
    )).toBe(true);
    expect(screen.queryByText("No saved candidates in this vacancy.")).not.toBeInTheDocument();
  });

  it("disables the shortlist action and surfaces the error when the shortlist state cannot be loaded", () => {
    shortlistQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      isSuccess: false,
      error: shortlistLoadError
    });

    render(
      <ShortlistSaveButton
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        candidateName="Alex Morgan"
      />
    );

    const button = screen.getByRole("button", { name: "Save Alex Morgan to shortlist" });
    expect(button).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    fireEvent.click(button);
    expect(saveMutate).not.toHaveBeenCalled();
  });

  it("disables the shortlist action while the persisted state is still loading", () => {
    shortlistQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      isSuccess: false
    });

    render(
      <ShortlistSaveButton
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        candidateName="Alex Morgan"
      />
    );

    const button = screen.getByRole("button", { name: "Save Alex Morgan to shortlist" });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(saveMutate).not.toHaveBeenCalled();
  });

  it("renders an empty shortlist state", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("No saved candidates yet.")).toBeInTheDocument();
  });

  it("renders existing shortlist entries with remove actions", async () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toHaveAttribute(
      "href",
      "/employer/matches/candidate-1?vacancy_id=vacancy-1"
    );
    expect(screen.queryByText("entry-1")).not.toBeInTheDocument();
    expect(screen.queryByText(/employer_id/)).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    );
    await waitFor(() => {
      expect(removeMutate).toHaveBeenCalledWith("candidate-1");
    });
  });

  it("keeps the backend shortlist order on the shortlist page", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [secondShortlistEntry, shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    const links = screen
      .getAllByRole("link", { name: /Review candidate/ })
      .map((link) => link.getAttribute("href"));
    expect(links).toEqual([
      "/employer/matches/candidate-2?vacancy_id=vacancy-1",
      "/employer/matches/candidate-1?vacancy_id=vacancy-1"
    ]);
  });

  it("falls back safely when a saved candidate has no current match data", () => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          {
            ...shortlistEntry,
            id: "entry-3",
            candidate_id: "candidate-unmatched"
          }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByText("Saved candidate")).toBeInTheDocument();
    expect(screen.queryByText("candidate-unmatched")).not.toBeInTheDocument();
    expect(screen.queryByText("entry-3")).not.toBeInTheDocument();
  });

  it("shows a shortlist page error instead of pretending the shortlist is empty", () => {
    shortlistQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      isSuccess: false,
      error: shortlistLoadError,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    expect(screen.queryByText("No saved candidates yet.")).not.toBeInTheDocument();
  });
});

describe("Shortlist API client contract", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("calls the exact backend paths and handles the empty 204 DELETE response", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ entries: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(shortlistEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(listVacancyShortlist("vacancy-1")).resolves.toEqual({ entries: [] });
    await expect(saveCandidateToShortlist("vacancy-1", "candidate-1")).resolves.toEqual(
      shortlistEntry
    );
    await expect(
      removeCandidateFromShortlist("vacancy-1", "candidate-1")
    ).resolves.toBeUndefined();

    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/employer/vacancies/vacancy-1/shortlist");
    expect(fetchMock.mock.calls[0][1].method).toBe("GET");
    expect(fetchMock.mock.calls[1][0]).toBe(
      "/api/v1/employer/vacancies/vacancy-1/shortlist/candidate-1"
    );
    expect(fetchMock.mock.calls[1][1].method).toBe("PUT");
    expect(fetchMock.mock.calls[2][0]).toBe(
      "/api/v1/employer/vacancies/vacancy-1/shortlist/candidate-1"
    );
    expect(fetchMock.mock.calls[2][1].method).toBe("DELETE");
  });
});

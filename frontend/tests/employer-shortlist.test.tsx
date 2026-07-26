import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ShortlistNoteEditor } from "@/features/employer/shortlist-note-editor";
import { ShortlistSaveButton } from "@/features/employer/shortlist-save-button";
import { ShortlistStageControl } from "@/features/employer/shortlist-stage-control";
import { VacancyShortlistView } from "@/features/employer/vacancy-shortlist-view";
import { EmployerSection } from "@/features/employer-section";
import { CandidateProfileView } from "@/features/match-details/candidate-profile-view";
import {
  listVacancyShortlist,
  removeCandidateFromShortlist,
  saveCandidateToShortlist,
  updateEmployerShortlistNote,
  updateEmployerShortlistStage
} from "@/lib/api/employer";
import { ApiClientError } from "@/lib/api/error";
import type { EmployerShortlistEntry } from "@/lib/api/types/employer";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

const shortlistQuery = vi.fn();
const saveMutate = vi.fn();
const removeMutate = vi.fn();
const updateStageMutate = vi.fn();
const updateNoteMutate = vi.fn();
const saveState = vi.fn();
const removeState = vi.fn();
const updateStageState = vi.fn();
const updateNoteState = vi.fn();
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
  useVacancyApplicantsQuery: () => ({
    data: { applicants: [] },
    isLoading: false,
    isError: false,
    isSuccess: true,
    refetch: vi.fn()
  }),
  useApplicantContactQuery: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  }),
  useSaveCandidateToShortlist: () => saveState(),
  useRemoveCandidateFromShortlist: () => removeState(),
  useUpdateEmployerShortlistStage: () => updateStageState(),
  useUpdateEmployerShortlistNote: () => updateNoteState(),
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
  roadmap: [],
  has_applied: true
};

const shortlistEntry: EmployerShortlistEntry = {
  id: "entry-1",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-1",
  stage: "shortlisted",
  note: null,
  created_at: "2026-07-25T10:00:00Z",
  updated_at: "2026-07-25T10:00:00Z"
};

const secondShortlistEntry: EmployerShortlistEntry = {
  id: "entry-2",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-2",
  stage: "interview",
  note: null,
  created_at: "2026-07-25T11:00:00Z",
  updated_at: "2026-07-25T11:00:00Z"
};

const rejectedShortlistEntry: EmployerShortlistEntry = {
  id: "entry-rejected",
  vacancy_id: "vacancy-1",
  candidate_id: "candidate-1",
  stage: "rejected",
  note: null,
  created_at: "2026-07-25T10:00:00Z",
  updated_at: "2026-07-25T12:00:00Z"
};

const notedShortlistEntry: EmployerShortlistEntry = {
  ...shortlistEntry,
  note: "Strong backend experience"
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
    data: {
      id: "company-1",
      company_name: "Beyond",
      website: null,
      description: null,
      created_at: "2026-07-20T10:00:00Z"
    },
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
  updateStageMutate.mockReset();
  updateNoteMutate.mockReset();
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

  it("shows Saved badge and stage control in Candidate Review when the backend shortlist includes the candidate", () => {
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
    expect(screen.getAllByText("Shortlisted").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" })
    ).toHaveValue("shortlisted");
    expect(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    ).toBeInTheDocument();
    expect(screen.queryByText("employer_id")).not.toBeInTheDocument();
  });

  it("keeps interview and rejected candidates visible on the shortlist page", () => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          { ...shortlistEntry, stage: "interview" },
          { ...secondShortlistEntry, candidate_id: "candidate-2", stage: "rejected" }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    matchesQuery.mockReturnValue({
      data: { matches: orderedMatches },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    vacancyDetailQuery.mockReturnValue({
      data: vacancy,
      isLoading: false,
      isError: false
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review candidate Bea Chen" })).toBeInTheDocument();
  });

  it("shows Recommended Candidates and Applicants empty state with shortlist entry point", () => {
    readyEmployerWorkspace({ shortlistEntries: [shortlistEntry] });
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    expect(screen.getByRole("heading", { name: "Applicants" })).toBeInTheDocument();
    expect(screen.getByText("No applicants yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Shortlist" })).toHaveAttribute(
      "href",
      "/employer/vacancies/vacancy-1/shortlist"
    );
    expect(screen.getAllByRole("heading", { name: "Recommended Candidates" }).length).toBeGreaterThan(0);

    const linksAll = screen
      .getAllByRole("link", { name: /Review candidate/ })
      .map((link) => link.getAttribute("href"));
    expect(linksAll).toEqual([
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-2?vacancy_id=vacancy-1"
    ]);
  });

  it("keeps the existing recommended candidate order regardless of shortlist order", () => {
    readyEmployerWorkspace({
      shortlistEntries: [secondShortlistEntry, shortlistEntry]
    });
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    const recommendedLinks = screen
      .getAllByRole("link", { name: /Review candidate/ })
      .map((link) => link.getAttribute("href"));
    expect(recommendedLinks).toEqual([
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-2?vacancy_id=vacancy-1"
    ]);
  });

  it("surfaces a shortlist load error in the vacancy workspace without inventing applicants", () => {
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

    expect(screen.getByText("No applicants yet")).toBeInTheDocument();
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
            candidate_id: "candidate-unmatched",
            stage: "screening"
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
    expect(screen.getAllByText("Screening").length).toBeGreaterThanOrEqual(1);
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

  it("filters the shortlist page by hiring stage without changing backend order", () => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          secondShortlistEntry,
          shortlistEntry,
          { ...rejectedShortlistEntry, candidate_id: "candidate-unmatched", id: "entry-3" }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(
      screen.getAllByRole("link", { name: /Review candidate/ }).map((link) =>
        link.getAttribute("href")
      )
    ).toEqual([
      "/employer/matches/candidate-2?vacancy_id=vacancy-1",
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-unmatched?vacancy_id=vacancy-1"
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Interview" }));
    expect(screen.getByRole("link", { name: "Review candidate Bea Chen" })).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Review candidate Alex Morgan" })
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Offer" }));
    expect(screen.getByText("No candidates in Offer.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toBeInTheDocument();
  });

  it("changes hiring stage through the shortlist stage control", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    const select = screen.getByRole("combobox", {
      name: "Hiring stage for Alex Morgan"
    });
    expect(select).toHaveValue("shortlisted");
    expect(screen.getByRole("option", { name: "Interview" })).toBeInTheDocument();

    fireEvent.change(select, { target: { value: "shortlisted" } });
    expect(updateStageMutate).not.toHaveBeenCalled();

    fireEvent.change(select, { target: { value: "interview" } });
    expect(updateStageMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      stage: "interview"
    });
  });

  it("disables the stage select while a stage mutation is pending", () => {
    updateStageState.mockReturnValue({
      mutate: updateStageMutate,
      isPending: true,
      isError: false,
      error: null,
      variables: { candidateId: "candidate-1", stage: "interview" },
      reset: vi.fn()
    });

    render(
      <ShortlistStageControl
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        stage="shortlisted"
        candidateLabel="Alex Morgan"
      />
    );

    const select = screen.getByRole("combobox", {
      name: "Hiring stage for Alex Morgan"
    });
    expect(select).toBeDisabled();
    expect(select).toHaveAttribute("aria-busy", "true");
    expect(select).toHaveValue("shortlisted");
    fireEvent.change(select, { target: { value: "offer" } });
    expect(updateStageMutate).not.toHaveBeenCalled();
  });

  it("keeps the persisted stage visible and shows an alert when stage update fails", () => {
    updateStageState.mockReturnValue({
      mutate: updateStageMutate,
      isPending: false,
      isError: true,
      error: shortlistLoadError,
      variables: { candidateId: "candidate-1", stage: "interview" },
      reset: vi.fn()
    });

    render(
      <ShortlistStageControl
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        stage="shortlisted"
        candidateLabel="Alex Morgan"
      />
    );

    expect(screen.getByRole("combobox")).toHaveValue("shortlisted");
    expect(screen.getAllByText("Shortlisted").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
  });

  it("hides stage control for unsaved candidates and shows it after save state appears", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    const { rerender } = render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Alex Morgan to shortlist" })).toBeInTheDocument();

    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    rerender(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    ).toBeInTheDocument();
  });

  it("renders the persisted stage from props without keeping a stale local selection", () => {
    const { rerender } = render(
      <ShortlistStageControl
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        stage="shortlisted"
        candidateLabel="Alex Morgan"
      />
    );

    const select = screen.getByRole("combobox", {
      name: "Hiring stage for Alex Morgan"
    });
    fireEvent.change(select, { target: { value: "offer" } });
    expect(select).toHaveValue("shortlisted");
    expect(screen.getAllByText("Shortlisted").length).toBeGreaterThanOrEqual(1);

    rerender(
      <ShortlistStageControl
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        stage="offer"
        candidateLabel="Alex Morgan"
      />
    );

    expect(
      screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" })
    ).toHaveValue("offer");
    expect(screen.getAllByText("Offer").length).toBeGreaterThanOrEqual(1);
  });

  it.each([
    ["shortlisted", "Shortlisted"],
    ["screening", "Screening"],
    ["interview", "Interview"],
    ["offer", "Offer"],
    ["hired", "Hired"],
    ["rejected", "Rejected"]
  ] as const)("filters the shortlist page by the %s stage", (stage, label) => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          { ...shortlistEntry, stage },
          { ...secondShortlistEntry, stage: stage === "offer" ? "hired" : "offer" }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);
    fireEvent.click(screen.getByRole("button", { name: label }));

    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Review candidate Bea Chen" })
    ).not.toBeInTheDocument();
  });

  it("removes a non-default stage entry from the shortlist page", async () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [{ ...shortlistEntry, stage: "interview" }] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);
    fireEvent.click(
      screen.getByRole("button", { name: "Remove Alex Morgan from shortlist" })
    );
    await waitFor(() => {
      expect(removeMutate).toHaveBeenCalledWith("candidate-1");
    });
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

  it("PATCHes the hiring stage with the exact body and returns the server entry", async () => {
    const updatedEntry = {
      ...shortlistEntry,
      stage: "interview" as const,
      updated_at: "2026-07-26T12:00:00Z"
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(updatedEntry), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      updateEmployerShortlistStage("vacancy-1", "candidate-1", "interview")
    ).resolves.toEqual(updatedEntry);

    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/v1/employer/vacancies/vacancy-1/shortlist/candidate-1"
    );
    expect(fetchMock.mock.calls[0][1].method).toBe("PATCH");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({
      stage: "interview"
    });
  });

  it("propagates structured API errors from stage PATCH", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "SHORTLIST_ENTRY_NOT_FOUND",
              message: "Shortlist entry not found",
              details: [],
              request_id: "req-1"
            }
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(
      updateEmployerShortlistStage("vacancy-1", "candidate-1", "interview")
    ).rejects.toMatchObject({
      status: 404,
      code: "SHORTLIST_ENTRY_NOT_FOUND"
    });
  });
});

describe("Stage mutation cache", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("replaces only the matching entry, preserves order, and ignores failed mutations", async () => {
    const hooks = await vi.importActual<typeof import("@/lib/employer/hooks")>(
      "@/lib/employer/hooks"
    );
    const updatedEntry = {
      ...shortlistEntry,
      stage: "offer" as const,
      updated_at: "2026-07-26T15:00:00Z"
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(updatedEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "DATABASE_ERROR",
              message: "Database operation failed",
              details: [],
              request_id: "req-2"
            }
          }),
          { status: 500, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);

    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false }, queries: { retry: false } }
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [shortlistEntry, secondShortlistEntry]
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-2"), {
      entries: [{ ...shortlistEntry, vacancy_id: "vacancy-2", id: "entry-other" }]
    });

    function Probe() {
      const mutation = hooks.useUpdateEmployerShortlistStage("vacancy-1");
      const [error, setError] = useState<string | null>(null);
      return (
        <div>
          <button
            type="button"
            onClick={() =>
              mutation.mutate(
                { candidateId: "candidate-1", stage: "offer" },
                {
                  onError: (err) =>
                    setError(err instanceof ApiClientError ? err.message : "failed")
                }
              )
            }
          >
            apply
          </button>
          {error ? <p role="alert">{error}</p> : null}
        </div>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <Probe />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toEqual({
        entries: [updatedEntry, secondShortlistEntry]
      });
    });
    expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-2"))).toEqual({
      entries: [{ ...shortlistEntry, vacancy_id: "vacancy-2", id: "entry-other" }]
    });

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    });
    expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toEqual({
      entries: [updatedEntry, secondShortlistEntry]
    });

    vi.unstubAllGlobals();
  });

  it("does not seed an empty shortlist into a cache that was never loaded", async () => {
    const hooks = await vi.importActual<typeof import("@/lib/employer/hooks")>(
      "@/lib/employer/hooks"
    );
    const updatedEntry = { ...shortlistEntry, stage: "hired" as const };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(updatedEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
    );

    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false }, queries: { retry: false } }
    });

    function Probe() {
      const mutation = hooks.useUpdateEmployerShortlistStage("vacancy-1");
      return (
        <button
          type="button"
          onClick={() => mutation.mutate({ candidateId: "candidate-1", stage: "hired" })}
        >
          apply
        </button>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <Probe />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length
      ).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toBeUndefined();
    });
  });
});

describe("Shortlist note editor UI", () => {
  it("shows an empty labelled textarea with a disabled Save for a saved entry without a note", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    expect(textarea).toHaveValue("");
    expect(textarea).toHaveAttribute("maxlength", "5000");
    expect(screen.getByRole("button", { name: "Save note for Alex Morgan" })).toBeDisabled();
  });

  it("renders an existing server note in the textarea", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("Strong backend experience");
  });

  it("enables Save on typing and sends the outer-trimmed note without extra fields", () => {
    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    const saveButton = screen.getByRole("button", { name: "Save note for Alex Morgan" });
    expect(saveButton).toBeDisabled();

    fireEvent.change(textarea, { target: { value: "  Strong backend experience  " } });
    expect(saveButton).toBeEnabled();
    fireEvent.click(saveButton);

    expect(updateNoteMutate).toHaveBeenCalledTimes(1);
    expect(updateNoteMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      note: "Strong backend experience"
    });
  });

  it("preserves internal spaces and newlines when saving", () => {
    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    fireEvent.change(textarea, { target: { value: "a  b" } });
    fireEvent.click(screen.getByRole("button", { name: "Save note for Alex Morgan" }));
    expect(updateNoteMutate).toHaveBeenLastCalledWith({
      candidateId: "candidate-1",
      note: "a  b"
    });

    fireEvent.change(textarea, { target: { value: "a\n\nb" } });
    fireEvent.click(screen.getByRole("button", { name: "Save note for Alex Morgan" }));
    expect(updateNoteMutate).toHaveBeenLastCalledWith({
      candidateId: "candidate-1",
      note: "a\n\nb"
    });
  });

  it("sends null when the textarea is cleared and saved", () => {
    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="Strong backend experience"
        candidateLabel="Alex Morgan"
      />
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" }),
      { target: { value: "" } }
    );
    fireEvent.click(screen.getByRole("button", { name: "Save note for Alex Morgan" }));

    expect(updateNoteMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      note: null
    });
  });

  it("keeps Save disabled when the normalized draft equals the server note", () => {
    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="text"
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    const saveButton = screen.getByRole("button", { name: "Save note for Alex Morgan" });

    fireEvent.change(textarea, { target: { value: " text " } });
    expect(saveButton).toBeDisabled();
    fireEvent.click(saveButton);
    expect(updateNoteMutate).not.toHaveBeenCalled();
  });

  it("treats a whitespace-only draft over a null server note as unchanged", () => {
    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    const saveButton = screen.getByRole("button", { name: "Save note for Alex Morgan" });

    fireEvent.change(textarea, { target: { value: "   " } });
    expect(saveButton).toBeDisabled();
    fireEvent.click(saveButton);
    expect(updateNoteMutate).not.toHaveBeenCalled();
  });

  it("disables the textarea and Save with aria-busy while the note mutation is pending", () => {
    updateNoteState.mockReturnValue({
      mutate: updateNoteMutate,
      isPending: true,
      isError: false,
      error: null,
      variables: { candidateId: "candidate-1", note: "Strong backend experience" },
      reset: vi.fn()
    });

    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    const saveButton = screen.getByRole("button", { name: "Save note for Alex Morgan" });
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveAttribute("aria-busy", "true");
    expect(saveButton).toBeDisabled();
    expect(saveButton).toHaveAttribute("aria-busy", "true");
    fireEvent.click(saveButton);
    expect(updateNoteMutate).not.toHaveBeenCalled();
  });

  it("shows a note error as role alert and keeps the draft editable", () => {
    updateNoteState.mockReturnValue({
      mutate: updateNoteMutate,
      isPending: false,
      isError: true,
      error: shortlistLoadError,
      variables: { candidateId: "candidate-1", note: "Draft to retry" },
      reset: vi.fn()
    });

    render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    fireEvent.change(textarea, { target: { value: "Draft to retry" } });
    expect(textarea).toHaveValue("Draft to retry");
    const saveButton = screen.getByRole("button", { name: "Save note for Alex Morgan" });
    expect(saveButton).toBeEnabled();
    fireEvent.click(saveButton);
    expect(updateNoteMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      note: "Draft to retry"
    });
  });

  it("syncs the draft with the normalized server note after a successful save", () => {
    const { rerender } = render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    const textarea = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    fireEvent.change(textarea, { target: { value: "  note text  " } });

    rerender(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="note text"
        candidateLabel="Alex Morgan"
      />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("note text");
    expect(screen.getByRole("button", { name: "Save note for Alex Morgan" })).toBeDisabled();
  });

  it("keeps the user draft on unrelated rerenders with an unchanged server note", () => {
    const { rerender } = render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="server note"
        candidateLabel="Alex Morgan"
      />
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" }),
      { target: { value: "user draft in progress" } }
    );

    rerender(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="server note"
        candidateLabel="Alex Morgan"
      />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("user draft in progress");
  });

  it("resets the draft when candidateId changes even if the server note is identical", () => {
    const { rerender } = render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="shared note"
        candidateLabel="Alex Morgan"
      />
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" }),
      { target: { value: "draft for Alex only" } }
    );

    rerender(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-2"
        note="shared note"
        candidateLabel="Bea Chen"
      />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Bea Chen" })
    ).toHaveValue("shared note");
    expect(screen.queryByDisplayValue("draft for Alex only")).not.toBeInTheDocument();
  });

  it("keeps independent drafts for two shortlist entries that share the same initial note", () => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          { ...shortlistEntry, note: "same note" },
          { ...secondShortlistEntry, note: "same note" }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    const alexNote = screen.getByRole("textbox", {
      name: "Private note for Alex Morgan"
    });
    const beaNote = screen.getByRole("textbox", {
      name: "Private note for Bea Chen"
    });
    expect(alexNote).toHaveValue("same note");
    expect(beaNote).toHaveValue("same note");

    fireEvent.change(alexNote, { target: { value: "Alex draft" } });
    fireEvent.change(beaNote, { target: { value: "Bea draft" } });

    expect(alexNote).toHaveValue("Alex draft");
    expect(beaNote).toHaveValue("Bea draft");
    expect(
      screen.getByRole("button", { name: "Save note for Alex Morgan" })
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Save note for Bea Chen" })
    ).toBeEnabled();
  });

  it("uses the server-normalized note as draft source of truth, not the padded request payload", () => {
    const { rerender } = render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" }),
      { target: { value: "  padded request  " } }
    );
    fireEvent.click(screen.getByRole("button", { name: "Save note for Alex Morgan" }));
    expect(updateNoteMutate).toHaveBeenCalledWith({
      candidateId: "candidate-1",
      note: "padded request"
    });

    rerender(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="padded request"
        candidateLabel="Alex Morgan"
      />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("padded request");
    expect(
      screen.queryByDisplayValue("  padded request  ")
    ).not.toBeInTheDocument();
  });

  it("syncs the draft to null after a successful clear", () => {
    const { rerender } = render(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note="old note"
        candidateLabel="Alex Morgan"
      />
    );

    rerender(
      <ShortlistNoteEditor
        vacancyId="vacancy-1"
        candidateId="candidate-1"
        note={null}
        candidateLabel="Alex Morgan"
      />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("");
  });

  it("removes the note editor together with the entry after Remove", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    const { rerender } = render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);
    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toBeInTheDocument();

    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    rerender(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("keeps the stage filter working with note editors present", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry, secondShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });

    render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    fireEvent.click(screen.getByRole("button", { name: "Interview" }));
    expect(
      screen.getByRole("textbox", { name: "Private note for Bea Chen" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("textbox", { name: "Private note for Alex Morgan" })
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("Strong backend experience");
  });

  it("renders both the stage control and the saved note after a stage change rerender", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    const { rerender } = render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    shortlistQuery.mockReturnValue({
      data: { entries: [{ ...notedShortlistEntry, stage: "interview" }] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    rerender(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(
      screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" })
    ).toHaveValue("interview");
    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("Strong backend experience");
  });

  it("renders both the note and the stage after a note change rerender", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [{ ...shortlistEntry, stage: "offer" }] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    const { rerender } = render(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    shortlistQuery.mockReturnValue({
      data: { entries: [{ ...shortlistEntry, stage: "offer", note: "New note" }] },
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: vi.fn()
    });
    rerender(<VacancyShortlistView vacancyId="vacancy-1" enabled />);

    expect(
      screen.getByRole("combobox", { name: "Hiring stage for Alex Morgan" })
    ).toHaveValue("offer");
    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("New note");
  });
});

describe("Candidate Review note editor", () => {
  it("shows the note editor with an empty textarea for a saved candidate without a note", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });

    render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("");
  });

  it("shows the existing server note for a saved candidate", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });

    render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("Strong backend experience");
  });

  it("hides the note editor for an unsaved candidate and shows it after saving", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    const { rerender } = render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

    shortlistQuery.mockReturnValue({
      data: { entries: [shortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    rerender(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toHaveValue("");
  });

  it("hides the note editor after the candidate is removed from the shortlist", () => {
    shortlistQuery.mockReturnValue({
      data: { entries: [notedShortlistEntry] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    const { rerender } = render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );
    expect(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" })
    ).toBeInTheDocument();

    shortlistQuery.mockReturnValue({
      data: { entries: [] },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    rerender(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("does not carry a typed draft when Candidate Review switches to another saved candidate with the same note", () => {
    shortlistQuery.mockReturnValue({
      data: {
        entries: [
          { ...shortlistEntry, note: "shared note" },
          { ...secondShortlistEntry, note: "shared note" }
        ]
      },
      isLoading: false,
      isError: false,
      isSuccess: true
    });
    const { rerender } = render(
      <CandidateProfileView candidateId="candidate-1" vacancyId="vacancy-1" enabled />
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Private note for Alex Morgan" }),
      { target: { value: "Alex-only draft" } }
    );

    matchDetailsQuery.mockReturnValue({
      data: {
        ...matchDetails,
        candidate: {
          id: "candidate-2",
          name: "Bea Chen",
          headline: "Backend Engineer",
          avatar: null
        }
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    });
    rerender(
      <CandidateProfileView candidateId="candidate-2" vacancyId="vacancy-1" enabled />
    );

    expect(
      screen.getByRole("textbox", { name: "Private note for Bea Chen" })
    ).toHaveValue("shared note");
    expect(screen.queryByDisplayValue("Alex-only draft")).not.toBeInTheDocument();
  });
});

describe("Shortlist note API client contract", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("PATCHes the note endpoint with the exact body and returns the server entry", async () => {
    const updatedEntry = {
      ...shortlistEntry,
      note: "Strong backend experience",
      updated_at: "2026-07-26T12:00:00Z"
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(updatedEntry), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      updateEmployerShortlistNote("vacancy-1", "candidate-1", {
        note: "Strong backend experience"
      })
    ).resolves.toEqual(updatedEntry);

    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/v1/employer/vacancies/vacancy-1/shortlist/candidate-1/note"
    );
    expect(fetchMock.mock.calls[0][1].method).toBe("PATCH");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body).toEqual({ note: "Strong backend experience" });
    expect(Object.keys(body)).toEqual(["note"]);
  });

  it("sends exactly {\"note\": null} to clear the note", async () => {
    const clearedEntry = { ...shortlistEntry, note: null };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(clearedEntry), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      updateEmployerShortlistNote("vacancy-1", "candidate-1", { note: null })
    ).resolves.toEqual(clearedEntry);

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body).toEqual({ note: null });
    expect(Object.keys(body)).toEqual(["note"]);
  });

  it("propagates structured API errors from the note PATCH", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "SHORTLIST_ENTRY_NOT_FOUND",
              message: "Shortlist entry not found",
              details: [],
              request_id: "req-1"
            }
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(
      updateEmployerShortlistNote("vacancy-1", "candidate-1", { note: "x" })
    ).rejects.toMatchObject({
      status: 404,
      code: "SHORTLIST_ENTRY_NOT_FOUND"
    });
  });
});

describe("Note mutation cache", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("replaces the full entry from the server response, preserves order and stage, and ignores failures", async () => {
    const hooks = await vi.importActual<typeof import("@/lib/employer/hooks")>(
      "@/lib/employer/hooks"
    );
    const serverEntry = {
      ...shortlistEntry,
      stage: "interview" as const,
      note: "normalized server note",
      updated_at: "2026-07-26T15:00:00Z"
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(serverEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "DATABASE_ERROR",
              message: "Database operation failed",
              details: [],
              request_id: "req-2"
            }
          }),
          { status: 500, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);

    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false }, queries: { retry: false } }
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [{ ...shortlistEntry, stage: "interview" as const }, secondShortlistEntry]
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-2"), {
      entries: [{ ...shortlistEntry, vacancy_id: "vacancy-2", id: "entry-other" }]
    });

    function Probe() {
      const mutation = hooks.useUpdateEmployerShortlistNote("vacancy-1");
      const [error, setError] = useState<string | null>(null);
      return (
        <div>
          <button
            type="button"
            onClick={() =>
              mutation.mutate(
                { candidateId: "candidate-1", note: "  normalized server note  " },
                {
                  onError: (err) =>
                    setError(err instanceof ApiClientError ? err.message : "failed")
                }
              )
            }
          >
            apply
          </button>
          {error ? <p role="alert">{error}</p> : null}
        </div>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <Probe />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toEqual({
        entries: [serverEntry, secondShortlistEntry]
      });
    });
    expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-2"))).toEqual({
      entries: [{ ...shortlistEntry, vacancy_id: "vacancy-2", id: "entry-other" }]
    });

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Database operation failed");
    });
    expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toEqual({
      entries: [serverEntry, secondShortlistEntry]
    });

    vi.unstubAllGlobals();
  });

  it("stage mutation success keeps the note returned by the server", async () => {
    const hooks = await vi.importActual<typeof import("@/lib/employer/hooks")>(
      "@/lib/employer/hooks"
    );
    const serverEntry = {
      ...notedShortlistEntry,
      stage: "offer" as const,
      updated_at: "2026-07-26T16:00:00Z"
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(serverEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
    );

    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false }, queries: { retry: false } }
    });
    queryClient.setQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"), {
      entries: [notedShortlistEntry]
    });

    function Probe() {
      const mutation = hooks.useUpdateEmployerShortlistStage("vacancy-1");
      return (
        <button
          type="button"
          onClick={() => mutation.mutate({ candidateId: "candidate-1", stage: "offer" })}
        >
          apply
        </button>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <Probe />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toEqual({
        entries: [serverEntry]
      });
    });
  });

  it("does not seed an empty shortlist cache when the note mutation succeeds without a loaded cache", async () => {
    const hooks = await vi.importActual<typeof import("@/lib/employer/hooks")>(
      "@/lib/employer/hooks"
    );
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(notedShortlistEntry), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
    );

    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false }, queries: { retry: false } }
    });

    function Probe() {
      const mutation = hooks.useUpdateEmployerShortlistNote("vacancy-1");
      return (
        <button
          type="button"
          onClick={() =>
            mutation.mutate({ candidateId: "candidate-1", note: "Strong backend experience" })
          }
        >
          apply
        </button>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <Probe />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "apply" }));
    await waitFor(() => {
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length
      ).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(queryClient.getQueryData(hooks.vacancyShortlistQueryKey("vacancy-1"))).toBeUndefined();
    });
  });
});

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateVacancyCard } from "@/features/candidate-vacancies-section";
import type { CandidateVacancy } from "@/lib/api/types/candidate-vacancies";

const applyMutate = vi.fn();
const withdrawMutate = vi.fn();
const applyState = vi.fn();
const withdrawState = vi.fn();
const vacanciesQuery = vi.fn();

vi.mock("@/lib/candidate-vacancies/hooks", () => ({
  useCandidateVacanciesQuery: () => vacanciesQuery(),
  useCandidateVacancyQuery: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  }),
  useApplyToVacancy: () => applyState(),
  useWithdrawApplication: () => withdrawState()
}));

const baseVacancy: CandidateVacancy = {
  id: "vacancy-1",
  title: "Backend Engineer",
  company_name: "Acme",
  description: "Build APIs",
  created_at: "2026-07-20T10:00:00Z",
  required_skills: ["Python"],
  preferred_skills: ["Redis"],
  match: {
    score: 80,
    required: { matched: ["Python"], missing: [] },
    preferred: { matched: [], missing: ["Redis"] }
  },
  application: null
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Candidate vacancy apply actions", () => {
  it("shows Apply and calls apply mutation when there is no active application", () => {
    applyState.mockReturnValue({
      mutate: applyMutate,
      isPending: false,
      error: null
    });
    withdrawState.mockReturnValue({
      mutate: withdrawMutate,
      isPending: false,
      error: null
    });

    render(<CandidateVacancyCard vacancy={baseVacancy} />);

    const applyButton = screen.getByRole("button", { name: /Apply now/i });
    fireEvent.click(applyButton);
    expect(applyMutate).toHaveBeenCalledTimes(1);
    expect(withdrawMutate).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: /Withdraw/i })).not.toBeInTheDocument();
  });

  it("shows Withdraw and calls withdraw mutation when application status is applied", () => {
    applyState.mockReturnValue({
      mutate: applyMutate,
      isPending: false,
      error: null
    });
    withdrawState.mockReturnValue({
      mutate: withdrawMutate,
      isPending: false,
      error: null
    });

    render(
      <CandidateVacancyCard
        vacancy={{
          ...baseVacancy,
          application: {
            id: "application-1",
            vacancy_id: "vacancy-1",
            candidate_id: "candidate-1",
            status: "applied",
            created_at: "2026-07-25T10:00:00Z",
            updated_at: "2026-07-25T10:00:00Z"
          }
        }}
      />
    );

    expect(screen.getByText("Applied")).toBeInTheDocument();
    const withdrawButton = screen.getByRole("button", { name: /Withdraw/i });
    fireEvent.click(withdrawButton);
    expect(withdrawMutate).toHaveBeenCalledTimes(1);
    expect(applyMutate).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: /Apply now/i })).not.toBeInTheDocument();
  });

  it("shows Apply again when application status is withdrawn", () => {
    applyState.mockReturnValue({
      mutate: applyMutate,
      isPending: false,
      error: null
    });
    withdrawState.mockReturnValue({
      mutate: withdrawMutate,
      isPending: false,
      error: null
    });

    render(
      <CandidateVacancyCard
        vacancy={{
          ...baseVacancy,
          application: {
            id: "application-1",
            vacancy_id: "vacancy-1",
            candidate_id: "candidate-1",
            status: "withdrawn",
            created_at: "2026-07-25T10:00:00Z",
            updated_at: "2026-07-25T12:00:00Z"
          }
        }}
      />
    );

    const applyAgain = screen.getByRole("button", { name: /Apply again|Apply now/i });
    expect(applyAgain).toBeInTheDocument();
    expect(screen.queryByText("Applied")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Withdraw/i })).not.toBeInTheDocument();
  });

  it("keeps Apply as the primary CTA above View details", () => {
    applyState.mockReturnValue({
      mutate: applyMutate,
      isPending: false,
      error: null
    });
    withdrawState.mockReturnValue({
      mutate: withdrawMutate,
      isPending: false,
      error: null
    });

    render(<CandidateVacancyCard vacancy={baseVacancy} />);

    const apply = screen.getByRole("button", { name: /Apply now/i });
    const details = screen.getByRole("link", { name: /View details/i });
    expect(
      apply.compareDocumentPosition(details) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });
});

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EmployerSection } from "@/features/employer-section";

const companyQuery = vi.fn();
const vacanciesQuery = vi.fn();
const vacancyDetailQuery = vi.fn();
const requirementsQuery = vi.fn();
const matchesQuery = vi.fn();
const dashboardRequirements = vi.fn();
const dashboardMatches = vi.fn();

vi.mock("@tanstack/react-query", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-query")>()),
  useQueries: ({ queries }: { queries: Array<{ queryKey: readonly string[] }> }) => queries.map((query) => (
    query.queryKey.at(-1) === "requirements" ? dashboardRequirements(query.queryKey) : dashboardMatches(query.queryKey)
  ))
}));

vi.mock("@/lib/employer/hooks", () => ({
  useAddVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerCompany: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useCreateEmployerVacancy: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useDeleteVacancyRequirement: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useEmployerCompanyQuery: () => companyQuery(),
  useEmployerSkillsQuery: () => ({ data: [], isLoading: false, isError: false, isSuccess: true }),
  useEmployerVacanciesQuery: () => vacanciesQuery(),
  useEmployerVacancyQuery: () => vacancyDetailQuery(),
  useVacancyMatchesQuery: () => matchesQuery(),
  useVacancyRequirementsQuery: () => requirementsQuery(),
  vacancyMatchesQueryKey: (vacancyId: string) => ["employer", "vacancy", vacancyId, "matches"],
  vacancyRequirementsQueryKey: (vacancyId: string) => ["employer", "vacancy", vacancyId, "requirements"]
}));

const vacancy = {
  id: "vacancy-1",
  title: "Frontend Engineer",
  description: "Build product UI",
  status: "open" as const,
  created_at: "2026-07-20T10:00:00Z"
};

const configuredRequirements = [
  { id: "requirement-1", skill_id: "skill-react", skill_name: "React", skill_category: "frontend", requirement_type: "required" as const },
  { id: "requirement-2", skill_id: "skill-jest", skill_name: "Jest", skill_category: "testing", requirement_type: "preferred" as const }
];

const orderedMatches = [
  { candidate_id: "candidate-1", candidate_name: "Alex Morgan", score: 82, required: { matched: ["React"], missing: [] }, preferred: { matched: [], missing: ["Jest"] } },
  { candidate_id: "candidate-2", candidate_name: "Bea Chen", score: 74, required: { matched: ["React"], missing: [] }, preferred: { matched: ["Jest"], missing: [] } }
];

function readyVacancy({ requirements = configuredRequirements, matches = orderedMatches } = {}) {
  companyQuery.mockReturnValue({ data: { company_name: "Beyond", website: null, description: null }, isLoading: false, isError: false });
  vacanciesQuery.mockReturnValue({ data: [vacancy], isLoading: false, isError: false, refetch: vi.fn() });
  vacancyDetailQuery.mockReturnValue({ data: vacancy, isLoading: false, isError: false });
  requirementsQuery.mockReturnValue({ data: requirements, isLoading: false, isError: false, isSuccess: true });
  matchesQuery.mockReturnValue({ data: { matches }, isLoading: false, isError: false, isSuccess: true, refetch: vi.fn() });
  dashboardRequirements.mockReturnValue({ data: requirements });
  dashboardMatches.mockReturnValue({ data: { matches } });
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Employer vacancy workflow", () => {
  it("presents one clear vacancy action and opens the configured requirements and candidate-match hierarchy", () => {
    readyVacancy();
    render(<EmployerSection enabled />);

    expect(screen.getByRole("heading", { name: "Active vacancies" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Manage vacancy" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit requirements" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "View Matches" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    const workspace = screen.getByText("Selected vacancy workspace").closest("section");
    expect(workspace).not.toBeNull();
    expect(workspace?.closest("ul")).toBeNull();
    expect(screen.getByText("Vacancy workspace")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Requirements" })).toBeInTheDocument();
    expect(screen.getAllByText("Required skills")).toHaveLength(3);
    expect(screen.getAllByText("Preferred skills")).toHaveLength(3);
    expect(screen.getAllByRole("heading", { name: "Candidate matches" })).toHaveLength(2);
    expect(screen.getByRole("progressbar", { name: "Alex Morgan vacancy match" })).toHaveAttribute("aria-valuenow", "82");
    expect(screen.getByRole("link", { name: "Review candidate Alex Morgan" })).toHaveAttribute("href", "/employer/matches/candidate-1?vacancy_id=vacancy-1");
    expect(screen.queryByText("AI Hiring Intelligence")).not.toBeInTheDocument();
  });

  it("makes empty requirements and empty matches explicit without inventing workflow states", () => {
    readyVacancy({ requirements: [], matches: [] });
    render(<EmployerSection enabled />);

    expect(screen.getByText("Frontend Engineer needs requirements")).toBeInTheDocument();
    expect(screen.getByText("Frontend Engineer has no matches yet")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    expect(screen.getByText("Requirements are not configured")).toBeInTheDocument();
    expect(screen.getByText("No candidate matches yet")).toBeInTheDocument();
    expect(screen.queryByText(/processing/i)).not.toBeInTheDocument();
  });

  it("preserves the existing candidate-match order when opening candidate reviews", () => {
    readyVacancy();
    render(<EmployerSection enabled />);
    fireEvent.click(screen.getByRole("button", { name: "Manage vacancy" }));

    expect(screen.getAllByRole("link", { name: /Review candidate/ }).map((link) => link.getAttribute("href"))).toEqual([
      "/employer/matches/candidate-1?vacancy_id=vacancy-1",
      "/employer/matches/candidate-2?vacancy_id=vacancy-1"
    ]);
  });

  it("uses the response associated with the selected vacancy without cross-populating another vacancy card", () => {
    const secondVacancy = { ...vacancy, id: "vacancy-2", title: "Platform Engineer" };
    const platformMatches = [{ candidate_id: "candidate-3", candidate_name: "Casey Singh", score: 91, required: { matched: ["Python"], missing: [] }, preferred: { matched: [], missing: [] } }];

    companyQuery.mockReturnValue({ data: { company_name: "Beyond", website: null, description: null }, isLoading: false, isError: false });
    vacanciesQuery.mockReturnValue({ data: [vacancy, secondVacancy], isLoading: false, isError: false, refetch: vi.fn() });
    vacancyDetailQuery.mockReturnValue({ data: secondVacancy, isLoading: false, isError: false });
    requirementsQuery.mockReturnValue({ data: configuredRequirements, isLoading: false, isError: false, isSuccess: true });
    matchesQuery.mockReturnValue({ data: { matches: platformMatches }, isLoading: false, isError: false, isSuccess: true, refetch: vi.fn() });
    dashboardRequirements.mockImplementation(() => ({ data: configuredRequirements }));
    dashboardMatches.mockImplementation((queryKey: readonly string[]) => ({ data: { matches: queryKey[2] === "vacancy-1" ? orderedMatches : platformMatches } }));

    render(<EmployerSection enabled />);
    const manageButtons = screen.getAllByRole("button", { name: "Manage vacancy" });
    fireEvent.click(manageButtons[0]);
    fireEvent.click(manageButtons[1]);

    expect(screen.getAllByText("Selected vacancy workspace")).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Review candidate Casey Singh" })).toHaveAttribute("href", "/employer/matches/candidate-3?vacancy_id=vacancy-2");
    expect(screen.queryByRole("link", { name: "Review candidate Alex Morgan" })).not.toBeInTheDocument();
  });
});

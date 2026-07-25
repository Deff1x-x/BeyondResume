import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import InterviewScorecardPage from "@/app/employer/matches/[candidateId]/scorecard/page";

const auth = vi.hoisted(() => ({
  useCurrentUser: vi.fn()
}));

const navigation = vi.hoisted(() => ({
  replace: vi.fn(),
  candidateId: "candidate-1",
  vacancyId: null as string | null
}));

vi.mock("@/lib/auth/hooks", () => ({
  useCurrentUser: () => auth.useCurrentUser(),
  useLogout: () => ({ mutate: vi.fn(), isPending: false })
}));

vi.mock("@/lib/auth/token", () => ({
  getAccessToken: () => "token"
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  useParams: () => ({ candidateId: navigation.candidateId }),
  usePathname: () => "/employer/matches/candidate-1/scorecard",
  useSearchParams: () => ({
    get: (key: string) => (key === "vacancy_id" ? navigation.vacancyId : null)
  })
}));

vi.mock("@/components/workspace-shell", () => ({
  WorkspaceShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

vi.mock("@/features/match-details/interview-scorecard-workspace", () => ({
  EmployerInterviewScorecardWorkspace: () => <div>Scorecard workspace</div>
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  navigation.vacancyId = null;
  navigation.candidateId = "candidate-1";
});

describe("Interview Scorecard page", () => {
  it("shows a safe state when vacancy_id is missing", async () => {
    auth.useCurrentUser.mockReturnValue({
      data: { id: "user-1", role: "employer", email: "employer@example.com" },
      isLoading: false,
      isError: false
    });
    navigation.vacancyId = null;

    render(<InterviewScorecardPage />);

    expect(await screen.findByText("Missing match context")).toBeInTheDocument();
    expect(screen.queryByText("Scorecard workspace")).not.toBeInTheDocument();
  });

  it("renders workspace when candidate and vacancy are present", async () => {
    auth.useCurrentUser.mockReturnValue({
      data: { id: "user-1", role: "employer", email: "employer@example.com" },
      isLoading: false,
      isError: false
    });
    navigation.vacancyId = "vacancy-1";

    render(<InterviewScorecardPage />);

    expect(await screen.findByText("Scorecard workspace")).toBeInTheDocument();
  });
});

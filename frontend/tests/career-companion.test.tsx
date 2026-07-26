import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CareerCompanionSection } from "@/features/career-companion/career-companion-section";
import { ApiClientError } from "@/lib/api/error";
import type { CareerCompanionPlan } from "@/lib/api/types/career-companion";

const getPlan = vi.hoisted(() => vi.fn());
const generatePlan = vi.hoisted(() => vi.fn());
const patchAction = vi.hoisted(() => vi.fn());
const chat = vi.hoisted(() => vi.fn());
const refresh = vi.hoisted(() => vi.fn());
const vacancies = vi.hoisted(() => vi.fn());
const profile = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/career-companion", () => ({
  getCareerCompanionPlan: () => getPlan(),
  generateCareerCompanionPlan: (...args: unknown[]) => generatePlan(...args),
  patchCareerCompanionAction: (...args: unknown[]) => patchAction(...args),
  postCareerCompanionChat: (...args: unknown[]) => chat(...args),
  refreshCareerCompanionFromEvidence: () => refresh()
}));

vi.mock("@/lib/candidate-vacancies/hooks", () => ({
  useCandidateVacanciesQuery: () => ({
    data: vacancies(),
    isLoading: false,
    isError: false
  })
}));

vi.mock("@/lib/candidate/hooks", () => ({
  useCandidateProfileQuery: () => ({
    data: profile(),
    isLoading: false,
    isError: false
  })
}));

function samplePlan(): CareerCompanionPlan {
  return {
    id: "plan-1",
    mode: "target_role",
    target_vacancy_id: null,
    target_role: "Backend Developer",
    status: "active",
    generation_mode: "fallback",
    summary: { headline: "Start with Docker evidence." },
    current_position: {
      goal_label: "Backend Developer",
      verified_skills: ["Python"],
      missing_required_skills: ["Docker"],
      readiness: "nearly_ready",
      strongest_projects: []
    },
    actions: [
      {
        id: "action-1",
        horizon: "fix_now",
        action_type: "build_new_project",
        status: "suggested",
        title: "Create evidence for Docker",
        description: "Build Docker evidence",
        why_it_matters: "Required in target vacancies",
        implementation_steps: ["Add Dockerfile"],
        expected_artifacts: ["Dockerfile"],
        verification_method: "Re-sync GitHub",
        estimated_effort: "medium",
        github_repository_id: null,
        project_label: null,
        current_target_impact: { summary: "Closes 1 required skill gap(s)." },
        career_growth_impact: {},
        priority_score: 40,
        priority_explanation: "Closes required gaps",
        sort_order: 0,
        skills: [
          { skill_id: "s1", skill_name: "Docker", role: "gap" },
          { skill_id: "s1", skill_name: "Docker", role: "potential_cover" }
        ]
      }
    ],
    progress_events: [
      {
        id: "evt-1",
        event_type: "plan_generated",
        title: "Career plan generated",
        detail: "Generated via fallback",
        payload: {},
        created_at: "2026-07-26T00:00:00Z"
      }
    ],
    chat_messages: []
  };
}

function renderSection() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  return render(
    <QueryClientProvider client={client}>
      <CareerCompanionSection enabled />
    </QueryClientProvider>
  );
}

describe("CareerCompanionSection", () => {
  beforeEach(() => {
    getPlan.mockReset();
    generatePlan.mockReset();
    patchAction.mockReset();
    chat.mockReset();
    refresh.mockReset();
    vacancies.mockReturnValue([]);
    profile.mockReturnValue({ target_role: "Backend Developer" });
  });

  afterEach(() => {
    cleanup();
  });

  it("shows generate form when no plan exists", async () => {
    getPlan.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "CAREER_COMPANION_NOT_FOUND",
        message: "No active career companion plan."
      })
    );
    renderSection();
    expect(await screen.findByText(/Generate your first personalized career plan./i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate .*plan/i })).toBeInTheDocument();
    expect(screen.getByText("Target vacancy")).toBeInTheDocument();
    expect(screen.getByText("Explore direction")).toBeInTheDocument();
  });

  it("renders a connected timeline and refuses complete-by-click controls", async () => {
    getPlan.mockResolvedValue(samplePlan());
    renderSection();
    expect(await screen.findByText("Create evidence for Docker")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Connected roadmap" })).toBeInTheDocument();
    expect(screen.getByText("Fix Now")).toBeInTheDocument();
    expect(screen.getByText("Recommended next step")).toBeInTheDocument();
    expect(screen.getByText("0 of 1 completed")).toBeInTheDocument();
    expect(screen.getByText("Overall progress")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByLabelText("Overall roadmap progress")).toHaveAttribute("aria-valuenow", "0");
    expect(screen.getByRole("button", { name: "Hide details" })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
    expect(screen.getByText(/Not verified until evidence is detected/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Complete$/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hide details" }));
    expect(screen.getByRole("button", { name: "Show details" })).toHaveAttribute(
      "aria-expanded",
      "false"
    );
    expect(screen.queryByText(/Not verified until evidence is detected/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Implementation steps")).not.toBeInTheDocument();
  });

  it("marks the first incomplete stage as the recommended next step", async () => {
    const plan = samplePlan();
    plan.actions = [
      {
        ...plan.actions[0],
        id: "done-1",
        status: "completed",
        title: "Completed Docker baseline",
        sort_order: 0
      },
      {
        ...plan.actions[0],
        id: "next-1",
        status: "suggested",
        title: "Add API tests",
        horizon: "build_next",
        sort_order: 1,
        skills: [{ skill_id: "s2", skill_name: "Testing", role: "gap" }]
      }
    ];
    getPlan.mockResolvedValue(plan);
    renderSection();

    expect(await screen.findByText("Add API tests")).toBeInTheDocument();
    expect(screen.getByText("1 of 2 completed")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByLabelText("Overall roadmap progress")).toHaveAttribute("aria-valuenow", "50");
    expect(screen.getByText("Recommended next step")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Step 2:.*Add API tests/i })).toBeInTheDocument();
  });

  it("posts the UI target_role payload contract", async () => {
    getPlan.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "CAREER_COMPANION_NOT_FOUND",
        message: "missing"
      })
    );
    generatePlan.mockResolvedValue(samplePlan());
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);
    fireEvent.change(screen.getByPlaceholderText("Backend Developer"), {
      target: { value: "Backend Developer" }
    });
    fireEvent.click(screen.getByRole("button", { name: /Generate .*plan/i }));
    await waitFor(() => {
      expect(generatePlan).toHaveBeenCalledWith({
        mode: "target_role",
        target_vacancy_id: null,
        target_role: "Backend Developer"
      });
    });
    expect(await screen.findByText("Create evidence for Docker")).toBeInTheDocument();
    expect(screen.queryByText(/Request failed/i)).not.toBeInTheDocument();
  });
});

describe("CareerCompanionSection mode selector", () => {
  beforeEach(() => {
    getPlan.mockReset();
    generatePlan.mockReset();
    patchAction.mockReset();
    chat.mockReset();
    refresh.mockReset();
    vacancies.mockReturnValue([
      {
        id: "vacancy-9",
        title: "Backend Engineer",
        company_name: "Acme",
        match: { score: 72 }
      }
    ]);
    profile.mockReturnValue({ target_role: "Backend Developer" });
    getPlan.mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "CAREER_COMPANION_NOT_FOUND",
        message: "missing"
      })
    );
  });

  afterEach(() => {
    cleanup();
  });

  function modeRadio(label: RegExp) {
    return screen.getByRole("radio", { name: label });
  }

  it("exposes the four modes as a keyboard-reachable radio group", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    expect(screen.getByRole("radiogroup", { name: /goal mode/i })).toBeInTheDocument();
    expect(screen.getAllByRole("radio")).toHaveLength(4);
    expect(modeRadio(/Target role/i)).toBeChecked();
    expect(modeRadio(/Target vacancy/i)).not.toBeChecked();
  });

  it("activates Target vacancy and shows the vacancy selector only", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.click(modeRadio(/Target vacancy/i));

    expect(modeRadio(/Target vacancy/i)).toBeChecked();
    expect(modeRadio(/Target role/i)).not.toBeChecked();
    expect(screen.getByLabelText("Vacancy")).toBeInTheDocument();
    expect(screen.queryByLabelText("Target role")).not.toBeInTheDocument();
  });

  it("activates Career growth and hides the target role input", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.click(modeRadio(/Career growth/i));

    expect(modeRadio(/Career growth/i)).toBeChecked();
    expect(screen.getByTestId("companion-career-growth-body")).toBeInTheDocument();
    expect(screen.queryByLabelText("Target role")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Vacancy")).not.toBeInTheDocument();
  });

  it("activates Explore direction and requires no manual target role", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.click(modeRadio(/Explore direction/i));

    expect(modeRadio(/Explore direction/i)).toBeChecked();
    expect(screen.getByTestId("companion-explore-direction-body")).toBeInTheDocument();
    expect(screen.queryByLabelText("Target role")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate .*plan/i })).toBeEnabled();
  });

  it("syncs the mode even when the radio is already checked in the DOM", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    // An out-of-sync DOM (e.g. browser form restoration) fires no change event.
    const explore = modeRadio(/Explore direction/i);
    (explore as HTMLInputElement).checked = true;
    fireEvent.click(explore);

    expect(explore).toBeChecked();
    expect(screen.getByTestId("companion-explore-direction-body")).toBeInTheDocument();
    expect(screen.queryByLabelText("Target role")).not.toBeInTheDocument();
  });

  it("activates a mode via keyboard interaction", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    const growth = modeRadio(/Career growth/i);
    growth.focus();
    expect(growth).toHaveFocus();
    fireEvent.keyDown(growth, { key: " " });
    fireEvent.click(growth);

    expect(growth).toBeChecked();
    expect(screen.getByTestId("companion-career-growth-body")).toBeInTheDocument();
  });

  it("sends target_vacancy_id and no target_role for Target vacancy", async () => {
    generatePlan.mockResolvedValue({ ...samplePlan(), mode: "target_vacancy" });
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.click(modeRadio(/Target vacancy/i));
    fireEvent.change(screen.getByLabelText("Vacancy"), { target: { value: "vacancy-9" } });
    fireEvent.click(screen.getByRole("button", { name: /Generate .*plan/i }));

    await waitFor(() => {
      expect(generatePlan).toHaveBeenCalledWith({
        mode: "target_vacancy",
        target_vacancy_id: "vacancy-9",
        target_role: null
      });
    });
  });

  it("disables generation until a vacancy is selected", async () => {
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.click(modeRadio(/Target vacancy/i));
    const cta = screen.getByRole("button", { name: /Generate .*plan/i });
    expect(cta).toBeDisabled();
    expect(screen.getByText(/Select a vacancy to generate a plan/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Vacancy"), { target: { value: "vacancy-9" } });
    expect(screen.getByRole("button", { name: /Generate .*plan/i })).toBeEnabled();
  });

  it("does not reuse a typed target role for Career growth or Explore direction", async () => {
    generatePlan.mockResolvedValue({ ...samplePlan(), mode: "career_growth" });
    renderSection();
    await screen.findByText(/Generate your first personalized career plan./i);

    fireEvent.change(screen.getByLabelText("Target role"), {
      target: { value: "Staff Platform Engineer" }
    });

    fireEvent.click(modeRadio(/Career growth/i));
    fireEvent.click(screen.getByRole("button", { name: /Generate .*plan/i }));
    await waitFor(() => {
      expect(generatePlan).toHaveBeenCalledWith({
        mode: "career_growth",
        target_vacancy_id: null,
        target_role: null
      });
    });

    generatePlan.mockClear();
    generatePlan.mockResolvedValue({ ...samplePlan(), mode: "explore_direction" });
    fireEvent.click(modeRadio(/Explore direction/i));
    fireEvent.click(screen.getByRole("button", { name: /Generate .*plan/i }));
    await waitFor(() => {
      expect(generatePlan).toHaveBeenCalledWith({
        mode: "explore_direction",
        target_vacancy_id: null,
        target_role: null
      });
    });
  });

  it("does not present a previous mode's plan as the current mode's result", async () => {
    getPlan.mockReset();
    getPlan.mockResolvedValue(samplePlan());
    renderSection();

    await screen.findByText("Create evidence for Docker");
    expect(screen.queryByTestId("companion-stale-plan-notice")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Regenerate .*plan/i })).toBeInTheDocument();

    fireEvent.click(modeRadio(/Explore direction/i));

    const notice = screen.getByTestId("companion-stale-plan-notice");
    expect(notice).toBeInTheDocument();
    expect(notice).toHaveTextContent(/saved target role plan/i);
    expect(screen.getByRole("button", { name: /Generate explore direction plan/i })).toBeInTheDocument();
  });
});

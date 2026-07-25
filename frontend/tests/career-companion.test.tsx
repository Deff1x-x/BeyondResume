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
    expect(await screen.findByText(/No active plan yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate plan/i })).toBeInTheDocument();
    expect(screen.getByText("Target vacancy")).toBeInTheDocument();
    expect(screen.getByText("Explore direction")).toBeInTheDocument();
  });

  it("renders horizons and refuses complete-by-click controls", async () => {
    getPlan.mockResolvedValue(samplePlan());
    renderSection();
    expect(await screen.findByText("Fix Now")).toBeInTheDocument();
    expect(screen.getByText("Create evidence for Docker")).toBeInTheDocument();
    expect(screen.getByText(/Not verified until evidence is detected/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Complete$/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept" })).toBeInTheDocument();
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
    await screen.findByText(/No active plan yet/i);
    fireEvent.change(screen.getByPlaceholderText("Backend Developer"), {
      target: { value: "Backend Developer" }
    });
    fireEvent.click(screen.getByRole("button", { name: /Generate plan/i }));
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

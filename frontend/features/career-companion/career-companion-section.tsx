"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SkeletonCard } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { CareerRoadmapOverview } from "@/features/career-companion/career-roadmap-overview";
import { CareerRoadmapTimeline } from "@/features/career-companion/career-roadmap-timeline";
import { ApiClientError } from "@/lib/api/error";
import type {
  CareerCompanionPlan,
  CompanionMode
} from "@/lib/api/types/career-companion";
import {
  useCareerCompanionChat,
  useCareerCompanionQuery,
  useGenerateCareerCompanion,
  usePatchCareerCompanionAction,
  useRefreshCareerCompanion
} from "@/lib/career-companion/hooks";
import { useCandidateVacanciesQuery } from "@/lib/candidate-vacancies/hooks";
import { useCandidateProfileQuery } from "@/lib/candidate/hooks";

const MODE_OPTIONS: Array<{ value: CompanionMode; label: string; help: string }> = [
  {
    value: "target_vacancy",
    label: "Target vacancy",
    help: "Plan against one open vacancy"
  },
  {
    value: "target_role",
    label: "Target role",
    help: "Plan for a profession, e.g. Backend Developer"
  },
  {
    value: "career_growth",
    label: "Career growth",
    help: "Prepare for stronger next-level vacancies"
  },
  {
    value: "explore_direction",
    label: "Explore direction",
    help: "See which direction fits your evidence"
  }
];

const MODE_LABELS: Record<CompanionMode, string> = {
  target_vacancy: "Target vacancy",
  target_role: "Target role",
  career_growth: "Career growth",
  explore_direction: "Explore direction"
};

const modeCardClass = (active: boolean) =>
  [
    "block cursor-pointer rounded-card border p-4 text-left transition-all duration-200 ease-out",
    "peer-focus-visible:ring-2 peer-focus-visible:ring-focus-ring peer-focus-visible:ring-offset-2",
    active
      ? "border-accent bg-accent/10 shadow-sm"
      : "border-border bg-background hover:border-border-strong"
  ].join(" ");

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "Career Companion could not be loaded. Please try again.";
}

function PlanView({
  plan,
  onStatus,
  onRefresh,
  refreshing
}: Readonly<{
  plan: CareerCompanionPlan;
  onStatus: (
    actionId: string,
    status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed"
  ) => void;
  onRefresh: () => void;
  refreshing: boolean;
}>) {
  const chat = useCareerCompanionChat();
  const [message, setMessage] = useState("");
  const position = plan.current_position ?? {};

  function onChat(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || chat.isPending) return;
    chat.mutate(trimmed, {
      onSuccess: () => setMessage("")
    });
  }

  return (
    <div className="space-y-8">
      <CareerRoadmapOverview plan={plan} onRefresh={onRefresh} refreshing={refreshing} />

      {(position.strongest_projects?.length ?? 0) > 0 ? (
        <p className="text-sm text-secondary">
          Strongest projects:{" "}
          {position.strongest_projects?.map((project) => project.label).join(", ")}
        </p>
      ) : null}

      <CareerRoadmapTimeline actions={plan.actions} onStatus={onStatus} />

      <section
        aria-labelledby="career-progress"
        className="rounded-card border border-border bg-surface p-5 shadow-card sm:p-6"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Progress</p>
        <h2 id="career-progress" className="mt-1 text-xl font-semibold tracking-tight text-ink">
          What changed
        </h2>
        {plan.progress_events.length === 0 ? (
          <p className="mt-3 text-sm text-secondary">
            No progress events yet. Re-sync GitHub after completing an action.
          </p>
        ) : (
          <ul className="mt-5 space-y-3">
            {[...plan.progress_events].reverse().slice(0, 8).map((event) => (
              <li key={event.id} className="rounded-card border border-border bg-surface-subtle/70 px-4 py-3">
                <p className="text-sm font-medium text-ink">{event.title}</p>
                <p className="mt-1 text-sm text-secondary">{event.detail}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        aria-labelledby="career-chat"
        className="rounded-card border border-border bg-surface p-5 shadow-card sm:p-6"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ai-muted">Companion dialog</p>
        <h2 id="career-chat" className="mt-1 text-xl font-semibold tracking-tight text-ink">
          Ask about this plan
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-secondary">
          Answers stay grounded in your evidence, gaps, and the actions above. You can also ask to
          shorten the plan or use only existing projects.
        </p>
        <div className="mt-5 space-y-3 rounded-card border border-border bg-background p-4">
          {plan.chat_messages.length === 0 ? (
            <p className="text-sm text-secondary">No messages yet.</p>
          ) : (
            <ul className="max-h-80 space-y-3 overflow-y-auto">
              {plan.chat_messages.map((item) => (
                <li
                  key={item.id}
                  className={
                    item.role === "user"
                      ? "rounded-control bg-primary/5 px-3 py-2 text-sm text-ink"
                      : "rounded-control bg-ai/10 px-3 py-2 text-sm text-ink"
                  }
                >
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-secondary">
                    {item.role}
                  </p>
                  <p className="mt-1 whitespace-pre-wrap leading-6">{item.content}</p>
                </li>
              ))}
            </ul>
          )}
          <form className="flex flex-col gap-3 sm:flex-row" onSubmit={onChat}>
            <Textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Why is this project recommended?"
              className="min-h-20 flex-1"
            />
            <Button type="submit" variant="primary" loading={chat.isPending} className="sm:self-end">
              Send
            </Button>
          </form>
          {chat.isError ? (
            <p className="text-sm text-danger" role="alert">
              {errorMessage(chat.error)}
            </p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

export function CareerCompanionSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const planQuery = useCareerCompanionQuery(enabled);
  const vacanciesQuery = useCandidateVacanciesQuery(enabled);
  const profileQuery = useCandidateProfileQuery(enabled);
  const generate = useGenerateCareerCompanion();
  const patchAction = usePatchCareerCompanionAction();
  const refresh = useRefreshCareerCompanion();

  const [mode, setMode] = useState<CompanionMode>("target_role");
  const [vacancyId, setVacancyId] = useState("");
  const [role, setRole] = useState("");

  const missingPlan =
    planQuery.isError &&
    planQuery.error instanceof ApiClientError &&
    planQuery.error.status === 404;

  const profileRole = profileQuery.data?.target_role ?? "";
  const vacancies = vacanciesQuery.data ?? [];
  const effectiveRole = role.trim() || profileRole;

  /**
   * Only the field the selected mode owns is submitted. Career growth and
   * explore direction deliberately send no target_role so the backend derives
   * the goal from evidence instead of a stale text input.
   */
  const payload = {
    mode,
    target_vacancy_id: mode === "target_vacancy" ? vacancyId || null : null,
    target_role: mode === "target_role" ? effectiveRole || null : null
  };

  const missingRequiredInput =
    (mode === "target_vacancy" && !vacancyId) ||
    (mode === "target_role" && !effectiveRole);

  const plan = planQuery.data;
  // A plan belongs to the current selection only when mode and target agree.
  const planMatchesSelection =
    plan !== undefined &&
    plan.mode === mode &&
    (mode !== "target_vacancy" || plan.target_vacancy_id === (vacancyId || null)) &&
    (mode !== "target_role" || !effectiveRole || plan.target_role === effectiveRole);

  function onGenerate(event: FormEvent) {
    event.preventDefault();
    if (missingRequiredInput || generate.isPending) {
      return;
    }
    generate.mutate(payload);
  }

  if (!enabled) return null;

  if (planQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading career companion" className="space-y-4">
        <SkeletonCard className="min-h-40" />
        <SkeletonCard className="min-h-56" />
      </div>
    );
  }

  if (planQuery.isError && !missingPlan) {
    return (
      <EmptyState
        role="alert"
        title="Career Companion unavailable"
        description={errorMessage(planQuery.error)}
        primaryAction={
          <Button type="button" variant="secondary" onClick={() => void planQuery.refetch()}>
            Try again
          </Button>
        }
      />
    );
  }

  return (
    <section
      id="career-companion-section"
      aria-labelledby="career-companion-title"
      className="scroll-mt-[var(--workspace-scroll-offset)] space-y-8"
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ai-muted">AI Career Companion</p>
        <h2 id="career-companion-title" className="mt-1 text-3xl font-semibold tracking-tight text-ink">
          Your evidence-guided growth plan
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-secondary">
          BeyondResume does not invent skills. It explains what blocks you now, which projects close multiple gaps, and what to learn for stronger vacancies — then verifies progress through evidence.
        </p>
      </div>

      <Card>
        <CardContent className="p-5 sm:p-6">
          <form className="space-y-4" autoComplete="off" onSubmit={onGenerate}>
            <div
              role="radiogroup"
              aria-label="Career Companion goal mode"
              className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
            >
              {MODE_OPTIONS.map((option) => (
                <label key={option.value} className="contents">
                  <input
                    type="radio"
                    name="companion-mode"
                    className="peer sr-only"
                    value={option.value}
                    checked={mode === option.value}
                    autoComplete="off"
                    onChange={() => setMode(option.value)}
                    // An already-checked radio fires no change event, so clicks sync too.
                    onClick={() => setMode(option.value)}
                  />
                  <span className={modeCardClass(mode === option.value)}>
                    <span className="block text-sm font-semibold text-ink">{option.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-secondary">
                      {option.help}
                    </span>
                  </span>
                </label>
              ))}
            </div>

            {mode === "target_vacancy" ? (
              <div className="space-y-2">
                <label htmlFor="companion-vacancy" className="text-sm font-medium text-ink">
                  Vacancy
                </label>
                <Select
                  id="companion-vacancy"
                  value={vacancyId}
                  onChange={(event) => setVacancyId(event.target.value)}
                  aria-describedby="companion-vacancy-help"
                >
                  <option value="">Select an open vacancy</option>
                  {vacancies.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title} · {item.company_name} · {item.match.score}%
                    </option>
                  ))}
                </Select>
                <p id="companion-vacancy-help" className="text-xs leading-5 text-secondary">
                  {vacancies.length === 0
                    ? "No open vacancies are available yet. Recommended vacancies appear here once published."
                    : "The plan uses the missing required and preferred skills of this vacancy."}
                </p>
              </div>
            ) : null}

            {mode === "target_role" ? (
              <div className="space-y-2">
                <label htmlFor="companion-role" className="text-sm font-medium text-ink">
                  Target role
                </label>
                <Input
                  id="companion-role"
                  value={role}
                  onChange={(event) => setRole(event.target.value)}
                  placeholder={profileRole || "Backend Developer"}
                  aria-describedby="companion-role-help"
                />
                <p id="companion-role-help" className="text-xs leading-5 text-secondary">
                  {profileRole
                    ? `Leave empty to use your profile target role (${profileRole}).`
                    : "Enter the profession you want this plan to target."}
                </p>
              </div>
            ) : null}

            {mode === "career_growth" ? (
              <div
                className="space-y-1 rounded-card border border-border bg-background p-4"
                data-testid="companion-career-growth-body"
              >
                <p className="text-sm font-medium text-ink">Next-level growth</p>
                <p className="text-xs leading-5 text-secondary">
                  {profileRole
                    ? `Uses your verified evidence and stronger vacancies above ${profileRole}. No target role input is needed.`
                    : "Uses your verified evidence and the stronger vacancies it already supports. No target role input is needed."}
                </p>
              </div>
            ) : null}

            {mode === "explore_direction" ? (
              <div
                className="space-y-1 rounded-card border border-border bg-background p-4"
                data-testid="companion-explore-direction-body"
              >
                <p className="text-sm font-medium text-ink">Evidence-based directions</p>
                <p className="text-xs leading-5 text-secondary">
                  Ranks the directions your verified skills and projects already support. No target
                  role is required.
                </p>
              </div>
            ) : null}

            <Button
              type="submit"
              variant="primary"
              loading={generate.isPending}
              disabled={missingRequiredInput}
              aria-label={`${planMatchesSelection ? "Regenerate" : "Generate"} ${MODE_LABELS[
                mode
              ].toLowerCase()} plan`}
            >
              {planMatchesSelection ? "Regenerate plan" : "Generate plan"}
            </Button>
            {missingRequiredInput ? (
              <p className="text-xs text-secondary">
                {mode === "target_vacancy"
                  ? "Select a vacancy to generate a plan."
                  : "Enter a target role to generate a plan."}
              </p>
            ) : null}
            {generate.isError ? (
              <p className="text-sm text-danger" role="alert">
                {errorMessage(generate.error)}
              </p>
            ) : null}
          </form>
        </CardContent>
      </Card>

      {missingPlan && !generate.isSuccess ? (
        <EmptyState
          icon={<Icon name="roadmap" className="h-8 w-8" />}
          title="Generate your first personalized career plan."
          description="Choose a goal above, then generate a plan. Career Companion explains gaps and next steps from your verified evidence — it does not invent skills."
        />
      ) : null}

      {generate.isPending ? (
        <div role="status" aria-label={`Generating ${MODE_LABELS[mode].toLowerCase()} plan`}>
          <SkeletonCard className="min-h-40" />
        </div>
      ) : null}

      {plan && !planMatchesSelection ? (
        <div
          role="status"
          data-testid="companion-stale-plan-notice"
          className="rounded-card border border-warning/30 bg-warning-soft p-4"
        >
          <p className="text-sm font-medium text-warning-muted">
            Showing your saved {MODE_LABELS[plan.mode].toLowerCase()} plan
          </p>
          <p className="mt-1 text-sm leading-6 text-warning-muted">
            This plan was generated for a different goal
            {plan.target_role ? ` (${plan.target_role})` : ""}. Generate a{" "}
            {MODE_LABELS[mode].toLowerCase()} plan to see results for your current selection.
          </p>
        </div>
      ) : null}

      {plan ? (
        <PlanView
          plan={plan}
          refreshing={refresh.isPending}
          onRefresh={() => refresh.mutate()}
          onStatus={(actionId, status) => patchAction.mutate({ actionId, status })}
        />
      ) : null}
    </section>
  );
}

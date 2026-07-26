"use client";

import { FormEvent, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SkeletonCard } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError } from "@/lib/api/error";
import type {
  ActionHorizon,
  ActionStatus,
  CareerCompanionAction,
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

const HORIZON_META: Record<ActionHorizon, { title: string; eyebrow: string }> = {
  fix_now: { title: "Fix Now", eyebrow: "Current blockers" },
  build_next: { title: "Build Next", eyebrow: "High-leverage projects" },
  grow_further: { title: "Grow Further", eyebrow: "Next career level" }
};

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "Career Companion could not be loaded. Please try again.";
}

function statusLabel(status: ActionStatus): string {
  return status.replaceAll("_", " ");
}

function ActionCard({
  action,
  onStatus
}: Readonly<{
  action: CareerCompanionAction;
  onStatus: (status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed") => void;
}>) {
  const gaps = action.skills.filter((skill) => skill.role === "gap");
  const potential = action.skills.filter((skill) => skill.role === "potential_cover");
  const impact = action.current_target_impact?.summary;
  const growth = action.career_growth_impact?.summary;

  return (
    <li className="surface-lift rounded-card border border-border bg-background p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={action.horizon === "fix_now" ? "danger" : action.horizon === "grow_further" ? "ai" : "primary"}>
              {action.action_type.replaceAll("_", " ")}
            </Badge>
            <Badge variant="neutral">{statusLabel(action.status)}</Badge>
            <Badge variant="neutral">{action.estimated_effort} effort</Badge>
          </div>
          <h3 className="mt-3 text-lg font-semibold tracking-tight text-ink">{action.title}</h3>
          {action.project_label ? (
            <p className="mt-1 text-sm text-secondary">Project: {action.project_label}</p>
          ) : null}
        </div>
        <p className="text-xs font-medium tabular-nums text-secondary">Priority {action.priority_score}</p>
      </div>

      <p className="mt-3 text-sm leading-6 text-secondary">{action.description}</p>
      <p className="mt-3 text-sm leading-6 text-ink">
        <span className="font-medium">Why it matters:</span> {action.why_it_matters}
      </p>

      {action.implementation_steps.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Implementation steps</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-ink">
            {action.implementation_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      ) : null}

      {action.expected_artifacts.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Expected artifacts</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {action.expected_artifacts.map((artifact) => (
              <li key={artifact}>
                <Badge variant="neutral">{artifact}</Badge>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {gaps.length > 0 || potential.length > 0 ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Related gaps</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {gaps.map((skill) => (
                <Badge key={`gap-${skill.skill_id}-${skill.skill_name}`} variant="warning">
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Potentially covered</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {potential.map((skill) => (
                <Badge key={`pot-${skill.skill_id}-${skill.skill_name}`} variant="accent">
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted">Not verified until evidence is detected.</p>
          </div>
        </div>
      ) : null}

      <div className="mt-4 space-y-2 text-sm text-secondary">
        {typeof impact === "string" ? <p>Current target impact: {impact}</p> : null}
        {typeof growth === "string" ? <p>Career growth impact: {growth}</p> : null}
        <p>Verification: {action.verification_method}</p>
        <p>Priority: {action.priority_explanation}</p>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {action.status === "suggested" ? (
          <Button type="button" variant="primary" size="sm" onClick={() => onStatus("accepted")}>
            Accept
          </Button>
        ) : null}
        {action.status === "accepted" || action.status === "suggested" ? (
          <Button type="button" variant="secondary" size="sm" onClick={() => onStatus("in_progress")}>
            Start
          </Button>
        ) : null}
        {action.status === "in_progress" ? (
          <Button type="button" variant="secondary" size="sm" onClick={() => onStatus("awaiting_evidence")}>
            Mark awaiting evidence
          </Button>
        ) : null}
        {action.status !== "dismissed" && action.status !== "completed" ? (
          <Button type="button" variant="ghost" size="sm" onClick={() => onStatus("dismissed")}>
            Dismiss
          </Button>
        ) : null}
      </div>
    </li>
  );
}

function HorizonSection({
  horizon,
  actions,
  onStatus
}: Readonly<{
  horizon: ActionHorizon;
  actions: CareerCompanionAction[];
  onStatus: (actionId: string, status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed") => void;
}>) {
  const meta = HORIZON_META[horizon];
  if (actions.length === 0) {
    return null;
  }
  return (
    <section aria-labelledby={`career-horizon-${horizon}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">{meta.eyebrow}</p>
      <h2 id={`career-horizon-${horizon}`} className="mt-1 text-2xl font-semibold tracking-tight text-ink">
        {meta.title}
      </h2>
      <ul className="mt-5 space-y-4">
        {actions.map((action) => (
          <ActionCard
            key={action.id}
            action={action}
            onStatus={(status) => onStatus(action.id, status)}
          />
        ))}
      </ul>
    </section>
  );
}

function PlanView({
  plan,
  onStatus,
  onRefresh,
  refreshing
}: Readonly<{
  plan: CareerCompanionPlan;
  onStatus: (actionId: string, status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed") => void;
  onRefresh: () => void;
  refreshing: boolean;
}>) {
  const position = plan.current_position ?? {};
  const byHorizon = useMemo(() => {
    const groups: Record<ActionHorizon, CareerCompanionAction[]> = {
      fix_now: [],
      build_next: [],
      grow_further: []
    };
    for (const action of plan.actions) {
      groups[action.horizon]?.push(action);
    }
    return groups;
  }, [plan.actions]);

  const chat = useCareerCompanionChat();
  const [message, setMessage] = useState("");

  function onChat(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || chat.isPending) return;
    chat.mutate(trimmed, {
      onSuccess: () => setMessage("")
    });
  }

  return (
    <div className="space-y-10">
      <Card className="border-accent/30 bg-accent/5">
        <CardContent className="p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-muted">Career goal</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">
                {position.goal_label || plan.target_role || "Career development"}
              </h2>
              <p className="mt-2 text-sm text-secondary">
                Mode: {plan.mode.replaceAll("_", " ")} · Generated via {plan.generation_mode}
              </p>
              {typeof plan.summary.headline === "string" ? (
                <p className="mt-3 max-w-3xl text-sm leading-6 text-ink">{plan.summary.headline}</p>
              ) : null}
            </div>
            <Button type="button" variant="secondary" loading={refreshing} onClick={onRefresh}>
              <Icon name="refresh" className="h-4 w-4" />
              Re-check evidence
            </Button>
          </div>
        </CardContent>
      </Card>

      <section aria-labelledby="career-current-position">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Current position</p>
        <h2 id="career-current-position" className="mt-1 text-2xl font-semibold tracking-tight text-ink">
          Where you stand
        </h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-secondary">Readiness</p>
              <p className="mt-2 font-semibold capitalize text-ink">{position.readiness?.replaceAll("_", " ") || "unknown"}</p>
              {typeof position.target_match_score === "number" ? (
                <p className="mt-1 text-sm text-secondary">Match {position.target_match_score}%</p>
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-secondary">Verified skills</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-ink">
                {position.verified_skills?.length ?? 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-secondary">Missing required</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-ink">
                {position.missing_required_skills?.length ?? 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-secondary">Strongest projects</p>
              <p className="mt-2 text-sm text-ink">
                {position.strongest_projects?.map((project) => project.label).join(", ") || "None connected"}
              </p>
            </CardContent>
          </Card>
        </div>
        {(position.missing_required_skills?.length ?? 0) > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {position.missing_required_skills?.map((skill) => (
              <Badge key={skill} variant="danger">
                {skill}
              </Badge>
            ))}
          </div>
        ) : null}
        {(position.explore_directions?.length ?? 0) > 0 ? (
          <p className="mt-4 text-sm text-secondary">
            Evidence-aligned directions: {position.explore_directions?.join(" · ")}
          </p>
        ) : null}
      </section>

      <HorizonSection horizon="fix_now" actions={byHorizon.fix_now} onStatus={onStatus} />
      <HorizonSection horizon="build_next" actions={byHorizon.build_next} onStatus={onStatus} />
      <HorizonSection horizon="grow_further" actions={byHorizon.grow_further} onStatus={onStatus} />

      <section aria-labelledby="career-progress">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Progress</p>
        <h2 id="career-progress" className="mt-1 text-2xl font-semibold tracking-tight text-ink">
          What changed
        </h2>
        {plan.progress_events.length === 0 ? (
          <p className="mt-3 text-sm text-secondary">No progress events yet. Re-sync GitHub after completing an action.</p>
        ) : (
          <ul className="mt-5 space-y-3">
            {[...plan.progress_events].reverse().slice(0, 8).map((event) => (
              <li key={event.id} className="rounded-card border border-border bg-surface px-4 py-3">
                <p className="text-sm font-medium text-ink">{event.title}</p>
                <p className="mt-1 text-sm text-secondary">{event.detail}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="career-chat">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ai-muted">Companion dialog</p>
        <h2 id="career-chat" className="mt-1 text-2xl font-semibold tracking-tight text-ink">
          Ask about this plan
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-secondary">
          Answers stay grounded in your evidence, gaps, and the actions above. You can also ask to shorten the plan or use only existing projects.
        </p>
        <div className="mt-5 space-y-3 rounded-card border border-border bg-surface p-4">
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
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-secondary">{item.role}</p>
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

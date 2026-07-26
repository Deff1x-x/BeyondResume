import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import type { CareerCompanionPlan } from "@/lib/api/types/career-companion";
import {
  completedRoadmapCount,
  countableRoadmapActions,
  overallRoadmapProgressPercent,
  roadmapGoalLabel,
  uniqueGapSkillNames
} from "@/features/career-companion/roadmap-progress";

export type CareerRoadmapOverviewProps = Readonly<{
  plan: CareerCompanionPlan;
  onRefresh: () => void;
  refreshing: boolean;
}>;

export function CareerRoadmapOverview({
  plan,
  onRefresh,
  refreshing
}: CareerRoadmapOverviewProps) {
  const position = plan.current_position ?? {};
  const countable = countableRoadmapActions(plan.actions);
  const completed = completedRoadmapCount(plan.actions);
  const progress = overallRoadmapProgressPercent(plan.actions);
  const gaps = uniqueGapSkillNames(plan.actions);
  const goal = roadmapGoalLabel(plan);
  const headline =
    typeof plan.summary.headline === "string" ? plan.summary.headline : null;

  return (
    <section
      className="overflow-hidden rounded-card border border-accent/30 bg-surface shadow-card"
      aria-labelledby="career-roadmap-overview-title"
    >
      <div className="border-b border-accent/20 bg-accent-soft/60 px-5 py-5 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-accent text-accent-foreground"
                aria-hidden="true"
              >
                <Icon name="roadmap" className="h-4 w-4" />
              </span>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-muted">
                Career roadmap
              </p>
            </div>
            <h2
              id="career-roadmap-overview-title"
              className="mt-3 text-2xl font-semibold tracking-tight text-ink"
            >
              {goal}
            </h2>
            <p className="mt-2 text-sm text-secondary">
              Mode: {plan.mode.replaceAll("_", " ")} · Generated via {plan.generation_mode}
            </p>
            {headline ? (
              <p className="mt-3 max-w-3xl text-sm leading-6 text-ink">{headline}</p>
            ) : null}
          </div>
          <Button type="button" variant="secondary" loading={refreshing} onClick={onRefresh}>
            <Icon name="refresh" className="h-4 w-4" />
            Re-check evidence
          </Button>
        </div>
      </div>

      <div className="grid gap-4 border-b border-border px-5 py-5 sm:grid-cols-2 sm:px-6 xl:grid-cols-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">Steps</p>
          <p className="mt-2 text-sm font-semibold tabular-nums text-ink">
            {completed} of {countable.length} completed
          </p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">
            Skill gaps addressed
          </p>
          <p className="mt-2 text-sm font-semibold tabular-nums text-ink">
            {gaps.length} {gaps.length === 1 ? "skill gap" : "skill gaps"}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">Readiness</p>
          <p className="mt-2 text-sm font-semibold capitalize text-ink">
            {position.readiness?.replaceAll("_", " ") || "unknown"}
            {typeof position.target_match_score === "number"
              ? ` · Match ${position.target_match_score}%`
              : ""}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">
            Verified skills
          </p>
          <p className="mt-2 text-sm font-semibold tabular-nums text-ink">
            {position.verified_skills?.length ?? 0}
          </p>
        </div>
      </div>

      {progress !== null ? (
        <div className="px-5 py-4 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-ink">Overall progress</p>
            <p className="text-sm tabular-nums text-secondary" aria-live="polite">
              {progress}%
            </p>
          </div>
          <div
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-subtle"
            role="progressbar"
            aria-label="Overall roadmap progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : null}

      {gaps.length > 0 ? (
        <div className="border-t border-border px-5 py-4 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Gaps in this plan
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {gaps.map((skill) => (
              <Badge key={skill} variant="warning">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {(position.missing_required_skills?.length ?? 0) > 0 ? (
        <div className="border-t border-border px-5 py-4 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Missing required skills
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {position.missing_required_skills?.map((skill) => (
              <Badge key={skill} variant="danger">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {(position.explore_directions?.length ?? 0) > 0 ? (
        <p className="border-t border-border px-5 py-4 text-sm text-secondary sm:px-6">
          Evidence-aligned directions: {position.explore_directions?.join(" · ")}
        </p>
      ) : null}
    </section>
  );
}

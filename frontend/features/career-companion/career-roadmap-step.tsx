"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import type { CareerCompanionAction } from "@/lib/api/types/career-companion";
import { cn } from "@/lib/cn";
import {
  evidenceStateForAction,
  evidenceStateLabel,
  HORIZON_META,
  implementationProgressText,
  statusLabel,
  type RoadmapStepVisualState
} from "@/features/career-companion/roadmap-progress";

export type CareerRoadmapStepProps = Readonly<{
  action: CareerCompanionAction;
  stepNumber: number;
  isLast: boolean;
  visualState: RoadmapStepVisualState;
  isRecommended: boolean;
  expanded: boolean;
  onToggle: () => void;
  onStatus: (status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed") => void;
}>;

function markerIcon(visualState: RoadmapStepVisualState) {
  if (visualState === "completed") return "check" as const;
  if (visualState === "blocked") return "lock" as const;
  if (visualState === "current") return "circle-dot" as const;
  return null;
}

function markerClass(visualState: RoadmapStepVisualState): string {
  if (visualState === "completed") {
    return "border-accent/40 bg-accent text-accent-foreground";
  }
  if (visualState === "current") {
    return "border-accent bg-accent text-accent-foreground ring-4 ring-accent/20";
  }
  if (visualState === "blocked") {
    return "border-warning/40 bg-warning-soft text-warning";
  }
  return "border-border bg-surface-subtle text-secondary";
}

function shellClass(visualState: RoadmapStepVisualState, isRecommended: boolean): string {
  if (visualState === "current" || isRecommended) {
    return "border-accent/35 bg-accent-soft/40 shadow-sm";
  }
  if (visualState === "completed") {
    return "border-success/20 bg-success-soft/40";
  }
  if (visualState === "blocked") {
    return "border-warning/25 bg-warning-soft/50";
  }
  return "border-border bg-surface";
}

function statusBadgeVariant(
  visualState: RoadmapStepVisualState
): "success" | "warning" | "neutral" | "primary" | "danger" {
  if (visualState === "completed") return "success";
  if (visualState === "current") return "primary";
  if (visualState === "blocked") return "warning";
  return "neutral";
}

function evidenceBadgeVariant(
  state: ReturnType<typeof evidenceStateForAction>
): "success" | "warning" | "neutral" | "ai" {
  if (state === "verified") return "success";
  if (state === "evidence_added") return "ai";
  if (state === "verification_pending") return "warning";
  return "neutral";
}

export function CareerRoadmapStep({
  action,
  stepNumber,
  isLast,
  visualState,
  isRecommended,
  expanded,
  onToggle,
  onStatus
}: CareerRoadmapStepProps) {
  const gaps = action.skills.filter((skill) => skill.role === "gap");
  const potential = action.skills.filter((skill) => skill.role === "potential_cover");
  const impact = action.current_target_impact?.summary;
  const growth = action.career_growth_impact?.summary;
  const evidenceState = evidenceStateForAction(action);
  const taskProgress = implementationProgressText(action);
  const icon = markerIcon(visualState);
  const detailsId = `career-roadmap-step-${action.id}-details`;
  const horizon = HORIZON_META[action.horizon];

  return (
    <li className="relative flex gap-3 sm:gap-4">
      <div className="relative flex w-8 shrink-0 flex-col items-center sm:w-10">
        <span
          className={cn(
            "z-[1] inline-flex h-8 w-8 items-center justify-center rounded-full border text-xs font-semibold tabular-nums sm:h-10 sm:w-10 sm:text-sm",
            markerClass(visualState)
          )}
          aria-hidden="true"
        >
          {icon ? <Icon name={icon} className="h-3.5 w-3.5 sm:h-4 sm:w-4" /> : stepNumber}
        </span>
        {!isLast ? (
          <span
            className={cn(
              "absolute top-8 bottom-0 w-px sm:top-10",
              visualState === "completed" ? "bg-accent/50" : "bg-border"
            )}
            aria-hidden="true"
          />
        ) : null}
      </div>

      <div className={cn("mb-4 min-w-0 flex-1 rounded-card border p-4 sm:mb-5 sm:p-5", shellClass(visualState, isRecommended))}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="neutral">{horizon.title}</Badge>
              <Badge variant={statusBadgeVariant(visualState)}>{statusLabel(action.status)}</Badge>
              {isRecommended ? (
                <Badge variant="accent" aria-label="Recommended next step">
                  Recommended next step
                </Badge>
              ) : null}
            </div>
            <h3 className="mt-2 text-base font-semibold tracking-tight text-ink sm:text-lg">
              <span className="sr-only">{`Step ${stepNumber}: `}</span>
              {action.title}
            </h3>
            <p className="mt-1 line-clamp-2 text-sm leading-6 text-secondary">{action.description}</p>
            {action.project_label ? (
              <p className="mt-1 text-xs text-muted">Project: {action.project_label}</p>
            ) : null}
          </div>
          <button
            type="button"
            className={cn(
              "inline-flex min-h-9 shrink-0 items-center gap-1.5 rounded-button border border-border bg-surface px-3 text-sm font-medium text-ink",
              "transition duration-200 hover:border-border-strong hover:bg-surface-subtle",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            )}
            aria-expanded={expanded}
            aria-controls={detailsId}
            onClick={onToggle}
          >
            {expanded ? "Hide details" : "Show details"}
            <Icon
              name="chevron-down"
              className={cn("h-4 w-4 transition-transform duration-200", expanded && "rotate-180")}
              aria-hidden="true"
            />
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {gaps.map((skill) => (
            <Badge key={`gap-${skill.skill_id}-${skill.skill_name}`} variant="warning">
              {skill.skill_name}
            </Badge>
          ))}
          {taskProgress ? (
            <span className="text-xs tabular-nums text-secondary">{taskProgress}</span>
          ) : null}
          <Badge variant="neutral">{action.estimated_effort} effort</Badge>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-control border border-border/80 bg-background/70 px-3 py-2">
          <Icon name="evidence" className="h-3.5 w-3.5 text-secondary" aria-hidden="true" />
          <span className="text-xs font-semibold uppercase tracking-[0.1em] text-secondary">
            Verification
          </span>
          <Badge variant={evidenceBadgeVariant(evidenceState)}>
            {evidenceStateLabel(evidenceState)}
          </Badge>
          <span className="min-w-0 text-xs leading-5 text-secondary">{action.verification_method}</span>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          {action.status === "suggested" ? (
            <Button type="button" variant="primary" size="sm" className="w-full sm:w-auto" onClick={() => onStatus("accepted")}>
              Accept
            </Button>
          ) : null}
          {action.status === "accepted" || action.status === "suggested" ? (
            <Button
              type="button"
              variant={action.status === "accepted" ? "primary" : "secondary"}
              size="sm"
              className="w-full sm:w-auto"
              onClick={() => onStatus("in_progress")}
            >
              Start
            </Button>
          ) : null}
          {action.status === "in_progress" ? (
            <Button
              type="button"
              variant="primary"
              size="sm"
              className="w-full sm:w-auto"
              onClick={() => onStatus("awaiting_evidence")}
            >
              Mark awaiting evidence
            </Button>
          ) : null}
          {action.status !== "dismissed" && action.status !== "completed" ? (
            <Button type="button" variant="ghost" size="sm" className="w-full sm:w-auto" onClick={() => onStatus("dismissed")}>
              Dismiss
            </Button>
          ) : null}
        </div>

        {expanded ? (
          <div id={detailsId} className="mt-4 space-y-4 border-t border-border pt-4">
            <p className="text-sm leading-6 text-ink">
              <span className="font-medium">Why it matters:</span> {action.why_it_matters}
            </p>

            <p className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">
              {action.action_type.replaceAll("_", " ")} · Priority {action.priority_score}
            </p>

            {action.implementation_steps.length > 0 ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
                  Implementation steps
                </p>
                <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-ink">
                  {action.implementation_steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
            ) : null}

            {action.expected_artifacts.length > 0 ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
                  Evidence to submit
                </p>
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
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
                    Closes skill gaps
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {gaps.map((skill) => (
                      <Badge key={`detail-gap-${skill.skill_id}-${skill.skill_name}`} variant="warning">
                        {skill.skill_name}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
                    Potentially covered
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {potential.map((skill) => (
                      <Badge key={`pot-${skill.skill_id}-${skill.skill_name}`} variant="accent">
                        {skill.skill_name}
                      </Badge>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-muted">
                    Not verified until evidence is detected.
                  </p>
                </div>
              </div>
            ) : null}

            <div className="space-y-2 text-sm text-secondary">
              {typeof impact === "string" ? <p>Supports target: {impact}</p> : null}
              {typeof growth === "string" ? <p>Career growth: {growth}</p> : null}
              <p>Priority: {action.priority_explanation}</p>
            </div>
          </div>
        ) : (
          <div id={detailsId} hidden />
        )}
      </div>
    </li>
  );
}

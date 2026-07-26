import type {
  ActionHorizon,
  ActionStatus,
  CareerCompanionAction,
  CareerCompanionPlan
} from "@/lib/api/types/career-companion";

export const HORIZON_ORDER: ActionHorizon[] = ["fix_now", "build_next", "grow_further"];

export const HORIZON_META: Record<ActionHorizon, { title: string; eyebrow: string }> = {
  fix_now: { title: "Fix Now", eyebrow: "Current blockers" },
  build_next: { title: "Build Next", eyebrow: "High-leverage projects" },
  grow_further: { title: "Grow Further", eyebrow: "Next career level" }
};

export type RoadmapStepVisualState = "completed" | "current" | "future" | "blocked";

export type EvidencePresentationState =
  | "no_evidence"
  | "evidence_added"
  | "verification_pending"
  | "verified";

const ACTIVE_STATUSES: ReadonlySet<ActionStatus> = new Set([
  "in_progress",
  "awaiting_evidence",
  "evidence_detected",
  "partially_verified"
]);

const INCOMPLETE_STATUSES: ReadonlySet<ActionStatus> = new Set([
  "suggested",
  "accepted",
  "in_progress",
  "awaiting_evidence",
  "evidence_detected",
  "partially_verified"
]);

export function statusLabel(status: ActionStatus): string {
  return status.replaceAll("_", " ");
}

export function isActionDismissed(action: CareerCompanionAction): boolean {
  return action.status === "dismissed";
}

export function isActionCompleted(action: CareerCompanionAction): boolean {
  return action.status === "completed";
}

export function orderedRoadmapActions(actions: CareerCompanionAction[]): CareerCompanionAction[] {
  const byHorizon = new Map<ActionHorizon, CareerCompanionAction[]>();
  for (const horizon of HORIZON_ORDER) {
    byHorizon.set(horizon, []);
  }
  for (const action of actions) {
    byHorizon.get(action.horizon)?.push(action);
  }
  const ordered: CareerCompanionAction[] = [];
  for (const horizon of HORIZON_ORDER) {
    const group = byHorizon.get(horizon) ?? [];
    group.sort((left, right) => left.sort_order - right.sort_order || left.priority_score - right.priority_score);
    ordered.push(...group);
  }
  return ordered;
}

/** Active (non-dismissed) steps used for progress denominator. */
export function countableRoadmapActions(actions: CareerCompanionAction[]): CareerCompanionAction[] {
  return orderedRoadmapActions(actions).filter((action) => !isActionDismissed(action));
}

export function completedRoadmapCount(actions: CareerCompanionAction[]): number {
  return countableRoadmapActions(actions).filter(isActionCompleted).length;
}

export function overallRoadmapProgressPercent(actions: CareerCompanionAction[]): number | null {
  const countable = countableRoadmapActions(actions);
  if (countable.length === 0) {
    return null;
  }
  return Math.round((completedRoadmapCount(actions) / countable.length) * 100);
}

export function uniqueGapSkillNames(actions: CareerCompanionAction[]): string[] {
  const names: string[] = [];
  const seen = new Set<string>();
  for (const action of orderedRoadmapActions(actions)) {
    for (const skill of action.skills) {
      if (skill.role !== "gap") continue;
      const key = skill.skill_name.trim().toLowerCase();
      if (!key || seen.has(key)) continue;
      seen.add(key);
      names.push(skill.skill_name);
    }
  }
  return names;
}

/**
 * Recommended next step: first in-progress-family stage, else first incomplete,
 * else null when the countable roadmap is finished.
 */
export function findRecommendedNextActionId(actions: CareerCompanionAction[]): string | null {
  const countable = countableRoadmapActions(actions);
  const active = countable.find((action) => ACTIVE_STATUSES.has(action.status));
  if (active) {
    return active.id;
  }
  const incomplete = countable.find((action) => INCOMPLETE_STATUSES.has(action.status));
  return incomplete?.id ?? null;
}

export function visualStateForAction(
  action: CareerCompanionAction,
  recommendedId: string | null
): RoadmapStepVisualState {
  if (action.status === "dismissed") {
    return "blocked";
  }
  if (action.status === "completed") {
    return "completed";
  }
  if (action.id === recommendedId) {
    return "current";
  }
  return "future";
}

export function evidenceStateForAction(action: CareerCompanionAction): EvidencePresentationState {
  if (action.status === "completed") {
    return "verified";
  }
  if (action.status === "evidence_detected" || action.status === "partially_verified") {
    return "evidence_added";
  }
  if (action.status === "awaiting_evidence") {
    return "verification_pending";
  }
  return "no_evidence";
}

export function evidenceStateLabel(state: EvidencePresentationState): string {
  if (state === "verified") return "Verified";
  if (state === "evidence_added") return "Evidence added";
  if (state === "verification_pending") return "Verification pending";
  return "No evidence";
}

export function roadmapGoalLabel(plan: CareerCompanionPlan): string {
  return (
    plan.current_position?.goal_label?.trim() ||
    plan.target_role?.trim() ||
    "Career development"
  );
}

export function implementationProgressText(action: CareerCompanionAction): string | null {
  const total = action.implementation_steps.length;
  if (total === 0) {
    return null;
  }
  if (action.status === "completed") {
    return `${total} of ${total} tasks complete`;
  }
  return `${total} ${total === 1 ? "task" : "tasks"}`;
}

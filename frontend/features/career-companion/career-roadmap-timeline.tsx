"use client";

import { useEffect, useMemo, useState } from "react";

import { CareerRoadmapStep } from "@/features/career-companion/career-roadmap-step";
import {
  findRecommendedNextActionId,
  orderedRoadmapActions,
  visualStateForAction
} from "@/features/career-companion/roadmap-progress";
import type { CareerCompanionAction } from "@/lib/api/types/career-companion";

export type CareerRoadmapTimelineProps = Readonly<{
  actions: CareerCompanionAction[];
  onStatus: (
    actionId: string,
    status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed"
  ) => void;
}>;

export function CareerRoadmapTimeline({ actions, onStatus }: CareerRoadmapTimelineProps) {
  const ordered = useMemo(() => orderedRoadmapActions(actions), [actions]);
  const recommendedId = useMemo(() => findRecommendedNextActionId(actions), [actions]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [seededPlanKey, setSeededPlanKey] = useState<string | null>(null);
  const planKey = ordered.map((action) => action.id).join("|");

  useEffect(() => {
    if (!recommendedId || seededPlanKey === planKey) {
      return;
    }
    setExpandedIds(new Set([recommendedId]));
    setSeededPlanKey(planKey);
  }, [planKey, recommendedId, seededPlanKey]);

  if (ordered.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-border bg-surface-subtle/60 px-5 py-8 text-center">
        <p className="text-sm font-medium text-ink">No roadmap stages yet</p>
        <p className="mt-2 text-sm text-secondary">
          Generate a plan to see a connected sequence of next steps.
        </p>
      </div>
    );
  }

  function toggle(actionId: string) {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(actionId)) {
        next.delete(actionId);
      } else {
        next.add(actionId);
      }
      return next;
    });
  }

  const allCompleted =
    recommendedId === null &&
    ordered.every((action) => action.status === "completed" || action.status === "dismissed");

  return (
    <section
      className="rounded-card border border-border bg-surface p-4 shadow-card sm:p-6"
      aria-labelledby="career-roadmap-timeline-title"
    >
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Growth journey
          </p>
          <h2
            id="career-roadmap-timeline-title"
            className="mt-1 text-xl font-semibold tracking-tight text-ink sm:text-2xl"
          >
            Connected roadmap
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
            Follow the stages in order. Expand a step for tasks, evidence, and skill details.
          </p>
        </div>
        {allCompleted ? (
          <p className="rounded-control border border-success/25 bg-success-soft px-3 py-2 text-sm font-medium text-success">
            Roadmap complete
          </p>
        ) : null}
      </div>

      <ol className="m-0 list-none p-0">
        {ordered.map((action, index) => {
          const isRecommended = action.id === recommendedId;
          return (
            <CareerRoadmapStep
              key={action.id}
              action={action}
              stepNumber={index + 1}
              isLast={index === ordered.length - 1}
              visualState={visualStateForAction(action, recommendedId)}
              isRecommended={isRecommended}
              expanded={expandedIds.has(action.id)}
              onToggle={() => toggle(action.id)}
              onStatus={(status) => onStatus(action.id, status)}
            />
          );
        })}
      </ol>
    </section>
  );
}

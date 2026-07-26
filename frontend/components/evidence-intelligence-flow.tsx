"use client";

import { useEffect, useId, useState } from "react";

import { Icon, type IconName } from "@/components/ui/icon";
import { cn } from "@/lib/cn";

export type EvidenceIntelligenceFlowState = "idle" | "loading" | "success" | "error";

type EvidenceIntelligenceFlowProps = Readonly<{
  state?: EvidenceIntelligenceFlowState;
  className?: string;
  /** Smaller spacing for tight empty states. */
  compact?: boolean;
  /** Dark panel surfaces (optional landing accents). */
  inverted?: boolean;
}>;

type StepId = "evidence" | "skills" | "match" | "ai";

type StepDefinition = {
  id: StepId;
  label: string;
  icon: IconName;
  tone: "evidence" | "verified" | "match" | "ai";
};

const STEPS: readonly StepDefinition[] = [
  { id: "evidence", label: "Evidence", icon: "evidence", tone: "evidence" },
  { id: "skills", label: "Verified Skills", icon: "passport", tone: "verified" },
  { id: "match", label: "Candidate Match", icon: "gauge", tone: "match" },
  { id: "ai", label: "AI Insight", icon: "spark", tone: "ai" }
] as const;

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function aiStatusLabel(state: EvidenceIntelligenceFlowState): string {
  switch (state) {
    case "loading":
      return "Generating";
    case "success":
      return "Complete";
    case "error":
      return "Unavailable";
    case "idle":
    default:
      return "Waiting";
  }
}

function flowDescription(state: EvidenceIntelligenceFlowState): string {
  const base =
    "Evidence Intelligence Flow: Evidence, Verified Skills, Candidate Match, then AI Insight.";
  switch (state) {
    case "loading":
      return `${base} Deterministic steps are ready. AI Insight is generating.`;
    case "success":
      return `${base} All steps complete. AI Insight is grounded in the prior evidence chain.`;
    case "error":
      return `${base} Deterministic steps remain complete. AI Insight is temporarily unavailable.`;
    case "idle":
    default:
      return `${base} Deterministic steps are ready. AI Insight is waiting to generate.`;
  }
}

/**
 * Compact branded chain: Evidence → Verified Skills → Candidate Match → AI Insight.
 * Plays a one-shot entrance (~700–1000ms). Subsequent state changes only update the AI node.
 */
export function EvidenceIntelligenceFlow({
  state = "idle",
  className,
  compact = false,
  inverted = false
}: EvidenceIntelligenceFlowProps) {
  const labelId = useId();
  const [phase, setPhase] = useState<"pending" | "playing" | "settled">("pending");

  useEffect(() => {
    if (prefersReducedMotion()) {
      setPhase("settled");
      return;
    }

    setPhase("playing");
    const timer = window.setTimeout(() => setPhase("settled"), 920);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div
      className={cn(
        "eif",
        compact && "eif--compact",
        inverted && "eif--inverted",
        className
      )}
      data-state={state}
      data-phase={phase}
      role="group"
      aria-labelledby={labelId}
    >
      <p id={labelId} className="sr-only">
        {flowDescription(state)}
      </p>

      <ol className="eif-track">
        {STEPS.map((step, index) => {
          const isAi = step.id === "ai";
          const nodeStatus = isAi
            ? state === "idle"
              ? "waiting"
              : state === "loading"
                ? "active"
                : state === "success"
                  ? "complete"
                  : "error"
            : "complete";

          const statusText = isAi ? aiStatusLabel(state) : "Ready";

          return (
            <li key={step.id} className="eif-item">
              {index > 0 ? (
                <div
                  className="eif-connector"
                  data-index={index}
                  aria-hidden="true"
                >
                  <span className="eif-line" />
                </div>
              ) : null}

              <div
                className="eif-step"
                data-step={step.id}
                data-tone={step.tone}
                data-status={nodeStatus}
              >
                <span className="eif-node" aria-hidden="true">
                  <Icon name={step.icon} className="eif-icon" />
                </span>
                <span className="eif-copy">
                  <span className="eif-label">{step.label}</span>
                  <span
                    className={cn(
                      "eif-status",
                      isAi ? "eif-status--visible" : "sr-only"
                    )}
                  >
                    {statusText}
                  </span>
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

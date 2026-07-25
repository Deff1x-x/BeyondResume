"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/cn";

type EvidenceFlowVisualProps = {
  className?: string;
  compact?: boolean;
  /** Dark panel (auth aside) */
  inverted?: boolean;
};

const STEPS = [
  { id: "sources", label: "Resume + GitHub", detail: "Raw signals" },
  { id: "units", label: "Evidence units", detail: "Structured proof" },
  { id: "skills", label: "Verified skills", detail: "Skill Passport" },
  { id: "match", label: "Candidate match", detail: "Transparent score" },
  { id: "ai", label: "AI hiring insights", detail: "Grounded analysis" }
] as const;

/**
 * Product storytelling visual: evidence → verified skills → match → AI.
 * Respects prefers-reduced-motion (shows final state immediately).
 */
export function EvidenceFlowVisual({
  className,
  compact = false,
  inverted = false
}: EvidenceFlowVisualProps) {
  const [step, setStep] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => {
      setReducedMotion(media.matches);
      if (media.matches) {
        setStep(STEPS.length - 1);
      }
    };
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);

  useEffect(() => {
    if (reducedMotion) return;
    const interval = window.setInterval(() => {
      setStep((current) => (current + 1) % STEPS.length);
    }, 1600);
    return () => window.clearInterval(interval);
  }, [reducedMotion]);

  const matchScore = step >= 3 ? 86 + (step >= 4 ? 2 : 0) : 0;
  const showVerified = step >= 2;
  const showAi = step >= 4;

  return (
    <div
      className={cn("relative w-full", className)}
      aria-hidden="true"
    >
      <div
        className={cn(
          "grid gap-3",
          compact ? "gap-2" : "gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center"
        )}
      >
        {/* Source column */}
        <div className="space-y-2">
          {["Resume.pdf", "github.com/alex"].map((label, index) => (
            <div
              key={label}
              className={cn(
                "evidence-flow-node px-3 py-2.5 text-xs font-medium",
                inverted
                  ? "border-white/15 bg-white/5 text-white"
                  : "text-ink",
                step >= 0 && "ring-1 ring-ai/30"
              )}
              style={{ transitionDelay: `${index * 60}ms` }}
            >
              {label}
            </div>
          ))}
        </div>

        {!compact ? (
          <div className="hidden justify-center sm:flex" aria-hidden="true">
            <svg width="40" height="72" viewBox="0 0 40 72" className="overflow-visible">
              <path
                d="M4 12 C20 12, 20 36, 36 36"
                className="evidence-flow-connector"
                data-active={step >= 1 ? "true" : "false"}
              />
              <path
                d="M4 60 C20 60, 20 36, 36 36"
                className="evidence-flow-connector"
                data-active={step >= 1 ? "true" : "false"}
              />
            </svg>
          </div>
        ) : null}

        {/* Evidence → skills stack */}
        <div className="space-y-2">
          <div
            className={cn(
              "evidence-flow-node px-4 py-3",
              inverted ? "border-white/15 bg-white/5" : "",
              step >= 1 && "ring-1 ring-ai/40"
            )}
          >
            <p
              className={cn(
                "text-[11px] font-medium",
                inverted ? "text-primary-200" : "text-secondary"
              )}
            >
              Evidence units
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {["PR #842", "System design", "OpenAPI"].map((unit, index) => (
                <span
                  key={unit}
                  className={cn(
                    "rounded-control px-2 py-0.5 text-[11px]",
                    inverted ? "bg-white/10 text-white" : "bg-surface-subtle text-ink",
                    step >= 1 && index <= step && "ring-1 ring-ai/50"
                  )}
                >
                  {unit}
                </span>
              ))}
            </div>
          </div>

          <div
            className={cn(
              "evidence-flow-node evidence-verified-glow px-4 py-3",
              inverted ? "border-white/15 bg-white/5" : "",
              showVerified && "ring-1 ring-verified/50"
            )}
            data-active={showVerified ? "true" : "false"}
          >
            <div className="flex items-center justify-between gap-2">
              <p
                className={cn(
                  "text-[11px] font-medium",
                  inverted ? "text-primary-200" : "text-secondary"
                )}
              >
                Verified skills
              </p>
              {showVerified ? (
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-badge border px-2 py-0.5 text-[10px] font-semibold",
                    inverted
                      ? "border-accent/40 bg-accent/20 text-accent-foreground"
                      : "border-verified/40 bg-verified/20 text-verified-muted"
                  )}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  Verified
                </span>
              ) : null}
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {["React", "TypeScript", "System design"].map((skill) => (
                <span
                  key={skill}
                  className={cn(
                    "rounded-control px-2 py-0.5 text-[11px] font-medium",
                    inverted ? "bg-white/10 text-white" : "bg-background text-ink",
                    showVerified && "border border-verified/30"
                  )}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Match + AI */}
      <div className={cn("mt-3 grid gap-2", compact ? "" : "sm:grid-cols-2")}>
        <div
          className={cn(
            "evidence-flow-node px-4 py-3",
            inverted ? "border-white/15 bg-white/5" : "",
            step >= 3 && "ring-1 ring-accent/40"
          )}
        >
          <p
            className={cn(
              "text-[11px] font-medium",
              inverted ? "text-primary-200" : "text-secondary"
            )}
          >
            Candidate match
          </p>
          <p
            className={cn(
              "mt-1 font-display text-2xl font-semibold tabular-nums",
              inverted ? "text-accent" : "text-ink"
            )}
          >
            {step >= 3 ? `${matchScore}%` : "—"}
          </p>
          <div
            className={cn(
              "mt-2 h-1.5 overflow-hidden rounded-full",
              inverted ? "bg-white/10" : "bg-surface-subtle"
            )}
            role="presentation"
          >
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-slow ease-emphasized motion-reduce:transition-none"
              style={{ width: step >= 3 ? `${matchScore}%` : "0%" }}
            />
          </div>
        </div>

        <div
          className={cn(
            "evidence-flow-node px-4 py-3 transition-opacity duration-normal",
            inverted ? "border-white/15 bg-white/5" : "",
            showAi ? "opacity-100 ring-1 ring-ai/40" : "opacity-40"
          )}
        >
          <p
            className={cn(
              "text-[11px] font-medium",
              inverted ? "text-primary-200" : "text-ai-muted"
            )}
          >
            AI hiring insight
          </p>
          <p
            className={cn(
              "mt-1 text-sm font-medium leading-5",
              inverted ? "text-white" : "text-ink"
            )}
          >
            {showAi
              ? "Strong evidence for TypeScript depth — probe system design trade-offs."
              : "Waiting for verified signals…"}
          </p>
        </div>
      </div>

      {/* Step legend */}
      <ol className="mt-4 flex flex-wrap gap-2" aria-hidden="true">
        {STEPS.map((item, index) => (
          <li
            key={item.id}
            className={cn(
              "rounded-badge border px-2.5 py-1 text-[10px] font-medium transition-colors duration-fast",
              index <= step
                ? inverted
                  ? "border-accent/40 bg-accent/15 text-accent"
                  : index === 4
                    ? "border-ai/40 bg-ai/10 text-ai-muted"
                    : "border-accent/40 bg-accent/15 text-accent-muted"
                : inverted
                  ? "border-white/10 text-primary-300"
                  : "border-border text-muted"
            )}
          >
            {item.label}
          </li>
        ))}
      </ol>
    </div>
  );
}

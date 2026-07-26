"use client";

import { useEffect, useId, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";
import { cn } from "@/lib/cn";
import { prefersReducedMotion } from "@/lib/navigation/scroll-spy";
import { ONBOARDING_TOUR_STEPS } from "@/lib/onboarding/types";

type TargetRect = {
  top: number;
  left: number;
  width: number;
  height: number;
};

function findTourTarget(label: string): HTMLElement | null {
  if (label === "overview") {
    return (
      document.querySelector<HTMLElement>('aside nav a[href="/"]') ??
      document.querySelector<HTMLElement>('header nav a[href="/"]')
    );
  }

  const links = Array.from(document.querySelectorAll<HTMLElement>("aside nav a, header nav a"));
  return links.find((link) => link.textContent?.trim() === label) ?? null;
}

export function OnboardingTour() {
  const { showTour, skipTour, completeTour } = useCandidateOnboarding();
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<TargetRect | null>(null);
  const titleId = useId();
  const descriptionId = useId();
  const step = ONBOARDING_TOUR_STEPS[index];
  const reducedMotion = useMemo(() => prefersReducedMotion(), []);

  useEffect(() => {
    if (!showTour) {
      return;
    }

    function measure() {
      if (!step) {
        return;
      }
      const target = findTourTarget(step.target);
      if (!target) {
        setRect(null);
        return;
      }
      const next = target.getBoundingClientRect();
      setRect({
        top: next.top,
        left: next.left,
        width: next.width,
        height: next.height
      });
      target.scrollIntoView?.({ block: "nearest", inline: "nearest", behavior: reducedMotion ? "auto" : "smooth" });
    }

    measure();
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, { passive: true });
    return () => {
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure);
    };
  }, [index, reducedMotion, showTour, step]);

  useEffect(() => {
    if (!showTour) {
      return;
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        skipTour();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [showTour, skipTour]);

  if (!showTour || !step) {
    return null;
  }

  const isLast = index >= ONBOARDING_TOUR_STEPS.length - 1;
  const tooltipStyle = rect
    ? {
        top: Math.min(window.innerHeight - 180, Math.max(16, rect.top + rect.height + 12)),
        left: Math.min(window.innerWidth - 320, Math.max(16, rect.left))
      }
    : { top: 96, left: 24 };

  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="false" aria-labelledby={titleId} aria-describedby={descriptionId}>
      <div className="absolute inset-0 bg-ink/25" aria-hidden="true" />
      {rect ? (
        <div
          aria-hidden="true"
          className={cn(
            "pointer-events-none absolute rounded-control ring-2 ring-accent ring-offset-2 ring-offset-background",
            !reducedMotion && "transition-all duration-normal ease-standard"
          )}
          style={{
            top: rect.top - 4,
            left: rect.left - 4,
            width: rect.width + 8,
            height: rect.height + 8
          }}
        />
      ) : null}

      <div
        className="absolute w-[min(20rem,calc(100vw-2rem))] rounded-card border border-border bg-surface p-4 shadow-float"
        style={tooltipStyle}
      >
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
          Tour {index + 1} / {ONBOARDING_TOUR_STEPS.length}
        </p>
        <h2 id={titleId} className="mt-1 text-base font-semibold text-ink">
          {step.title}
        </h2>
        <p id={descriptionId} className="mt-2 text-sm leading-6 text-secondary">
          {step.body}
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={skipTour}>
            Skip tour
          </Button>
          <div className="flex gap-2">
            {index > 0 ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => setIndex((value) => value - 1)}>
                Back
              </Button>
            ) : null}
            <Button
              type="button"
              size="sm"
              onClick={() => {
                if (isLast) {
                  completeTour();
                  return;
                }
                setIndex((value) => value + 1);
              }}
            >
              {isLast ? "Done" : "Next"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

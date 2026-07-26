"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";

type AnimatedCounterProps = {
  value: number;
  className?: string;
  durationMs?: number;
  suffix?: string;
  prefix?: string;
};

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Soft count-up for KPI metrics. Respects prefers-reduced-motion.
 */
export function AnimatedCounter({
  value,
  className,
  durationMs = 900,
  suffix = "",
  prefix = ""
}: AnimatedCounterProps) {
  const [display, setDisplay] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    if (prefersReducedMotion()) {
      setDisplay(value);
      setStarted(true);
      return;
    }

    if (typeof IntersectionObserver === "undefined") {
      setStarted(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setStarted(true);
          observer.disconnect();
        }
      },
      { threshold: 0.4 }
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [value]);

  useEffect(() => {
    if (!started) return;
    if (prefersReducedMotion()) {
      setDisplay(value);
      return;
    }

    const start = performance.now();
    const from = 0;
    const to = value;
    let frame = 0;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(from + (to - from) * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [durationMs, started, value]);

  return (
    <span ref={ref} className={cn("tabular-nums", className)}>
      {prefix}
      {display}
      {suffix}
    </span>
  );
}

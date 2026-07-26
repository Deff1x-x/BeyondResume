"use client";

import { useEffect, useRef, useState } from "react";

import {
  getScrollOffset,
  pickActiveSectionId,
  sectionIdFromHash
} from "@/lib/navigation/scroll-spy";

export type UseScrollSpyOptions = {
  /** Section element ids in document order (top → bottom). */
  sectionIds: readonly string[];
  /** When false, observers are torn down and the hook returns null. */
  enabled?: boolean;
  /**
   * During a user-initiated smooth scroll, lock the active id so the indicator
   * does not briefly jump through intermediate sections.
   */
  lockedSectionId?: string | null;
};

/**
 * Viewport scroll-spy powered by a single IntersectionObserver.
 * Observes only sections present in the DOM and recalculates a deterministic
 * active section whenever intersections change.
 */
export function useScrollSpy({
  sectionIds,
  enabled = true,
  lockedSectionId = null
}: UseScrollSpyOptions): string | null {
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const sectionIdsKey = sectionIds.join("\0");
  const sectionIdsRef = useRef(sectionIds);
  sectionIdsRef.current = sectionIds;

  useEffect(() => {
    if (!enabled || sectionIds.length === 0) {
      setActiveSectionId(null);
      return;
    }

    let cancelled = false;
    let frame = 0;
    let observer: IntersectionObserver | null = null;
    const observed = new Set<Element>();

    const resolve = () => {
      if (cancelled) {
        return;
      }
      const next = pickActiveSectionId(sectionIdsRef.current, { offset: getScrollOffset() });
      setActiveSectionId((prev) => (prev === next ? prev : next));
    };

    const scheduleResolve = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(resolve);
    };

    const ensureObserver = () => {
      if (observer) {
        return observer;
      }
      if (typeof IntersectionObserver === "undefined") {
        return null;
      }
      observer = new IntersectionObserver(scheduleResolve, {
        root: null,
        rootMargin: `-${getScrollOffset()}px 0px -45% 0px`,
        threshold: [0, 0.1, 0.25, 0.5, 0.75, 1]
      });
      return observer;
    };

    const syncObservedElements = () => {
      const activeObserver = ensureObserver();
      if (!activeObserver) {
        scheduleResolve();
        return;
      }
      const nextElements = new Set<Element>();

      for (const id of sectionIdsRef.current) {
        const element = document.getElementById(id);
        if (!element) {
          continue;
        }
        nextElements.add(element);
        if (!observed.has(element)) {
          activeObserver.observe(element);
          observed.add(element);
        }
      }

      for (const element of observed) {
        if (!nextElements.has(element)) {
          activeObserver.unobserve(element);
          observed.delete(element);
        }
      }

      scheduleResolve();
    };

    const hashSection = sectionIdFromHash(window.location.hash);
    if (hashSection && sectionIds.includes(hashSection)) {
      setActiveSectionId(hashSection);
    }

    syncObservedElements();

    const mutationObserver = new MutationObserver(syncObservedElements);
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    const onResize = () => scheduleResolve();
    const onScroll = () => scheduleResolve();
    window.addEventListener("resize", onResize, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("hashchange", scheduleResolve);

    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
      observer?.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("hashchange", scheduleResolve);
      observed.clear();
    };
  }, [enabled, sectionIdsKey, sectionIds]);

  if (!enabled) {
    return null;
  }

  if (lockedSectionId && sectionIds.includes(lockedSectionId)) {
    return lockedSectionId;
  }

  return activeSectionId;
}

/** Mobile sticky header (~5rem) overlays content; desktop has no overlay. */
export const SCROLL_OFFSET_MOBILE_PX = 80;
export const SCROLL_OFFSET_DESKTOP_PX = 16;

/** Narrow band near the top of the viewport used as the activation line. */
export const SCROLL_SPY_TOP_BAND_RATIO = 0.28;

export function getScrollOffset(viewportWidth = typeof window !== "undefined" ? window.innerWidth : 1024): number {
  return viewportWidth < 1024 ? SCROLL_OFFSET_MOBILE_PX : SCROLL_OFFSET_DESKTOP_PX;
}

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function resolveScrollBehavior(requested: ScrollBehavior = "smooth"): ScrollBehavior {
  return prefersReducedMotion() ? "auto" : requested;
}

/**
 * Deterministic active section: among sections whose top has crossed the
 * activation line, pick the one closest to that line (largest top). This is
 * independent of nav-array order and stays stable for tall sections.
 */
export function pickActiveSectionId(
  sectionIds: readonly string[],
  options: { offset?: number; activationLine?: number; getElement?: (id: string) => Element | null } = {}
): string | null {
  if (sectionIds.length === 0) {
    return null;
  }

  const getElement = options.getElement ?? ((id: string) => document.getElementById(id));
  const offset = options.offset ?? getScrollOffset();
  const activationLine =
    options.activationLine ??
    offset + (typeof window !== "undefined" ? window.innerHeight : 800) * SCROLL_SPY_TOP_BAND_RATIO;

  let activeId: string | null = null;
  let bestTop = -Infinity;
  let firstExisting: string | null = null;
  let firstTop = Infinity;

  for (const id of sectionIds) {
    const element = getElement(id);
    if (!element) {
      continue;
    }
    const top = element.getBoundingClientRect().top;
    if (top < firstTop) {
      firstTop = top;
      firstExisting = id;
    }
    if (top <= activationLine && top >= bestTop) {
      bestTop = top;
      activeId = id;
    }
  }

  return activeId ?? firstExisting;
}

export function scrollToSectionId(
  sectionId: string,
  options: { behavior?: ScrollBehavior; offset?: number } = {}
): boolean {
  const element = document.getElementById(sectionId);
  if (!element) {
    return false;
  }

  const offset = options.offset ?? getScrollOffset();
  const behavior = resolveScrollBehavior(options.behavior ?? "smooth");
  const top = window.scrollY + element.getBoundingClientRect().top - offset;

  window.scrollTo({ top: Math.max(0, top), behavior });
  return true;
}

export function sectionIdFromHash(hash: string): string | null {
  if (!hash || hash === "#") {
    return null;
  }
  const value = hash.startsWith("#") ? hash.slice(1) : hash;
  try {
    return decodeURIComponent(value) || null;
  } catch {
    return value || null;
  }
}

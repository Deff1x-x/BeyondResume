import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getScrollOffset,
  pickActiveSectionId,
  prefersReducedMotion,
  resolveScrollBehavior,
  SCROLL_OFFSET_DESKTOP_PX,
  SCROLL_OFFSET_MOBILE_PX,
  sectionIdFromHash,
  scrollToSectionId
} from "@/lib/navigation/scroll-spy";

afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

function mockRect(top: number, height = 400) {
  return {
    top,
    bottom: top + height,
    height,
    left: 0,
    right: 1000,
    width: 1000,
    x: 0,
    y: top,
    toJSON: () => ({})
  } as DOMRect;
}

describe("scroll-spy utilities", () => {
  it("uses mobile and desktop scroll offsets", () => {
    expect(getScrollOffset(500)).toBe(SCROLL_OFFSET_MOBILE_PX);
    expect(getScrollOffset(1280)).toBe(SCROLL_OFFSET_DESKTOP_PX);
  });

  it("picks the crossed section closest to the activation line regardless of array order", () => {
    const elements = new Map<string, { getBoundingClientRect: () => DOMRect }>([
      ["overview-section", { getBoundingClientRect: () => mockRect(-100) }],
      ["opportunities-section", { getBoundingClientRect: () => mockRect(40) }],
      ["github-section", { getBoundingClientRect: () => mockRect(500) }]
    ]);

    expect(
      pickActiveSectionId(["overview-section", "opportunities-section", "github-section"], {
        offset: 16,
        activationLine: 200,
        getElement: (id) => (elements.get(id) as unknown as Element) ?? null
      })
    ).toBe("opportunities-section");

    // Geometry wins even if GitHub is listed before Resume in the nav array.
    expect(
      pickActiveSectionId(["github-section", "resume-section"], {
        offset: 16,
        activationLine: 200,
        getElement: (id) => {
          if (id === "github-section") {
            return { getBoundingClientRect: () => mockRect(16) } as unknown as Element;
          }
          if (id === "resume-section") {
            return { getBoundingClientRect: () => mockRect(-400) } as unknown as Element;
          }
          return null;
        }
      })
    ).toBe("github-section");
  });

  it("falls back to the first existing section when none have crossed yet", () => {
    const elements = new Map<string, { getBoundingClientRect: () => DOMRect }>([
      ["overview-section", { getBoundingClientRect: () => mockRect(300) }],
      ["github-section", { getBoundingClientRect: () => mockRect(900) }]
    ]);

    expect(
      pickActiveSectionId(["overview-section", "github-section", "missing-section"], {
        offset: 16,
        activationLine: 200,
        getElement: (id) => (elements.get(id) as unknown as Element) ?? null
      })
    ).toBe("overview-section");
  });

  it("ignores missing sections", () => {
    expect(
      pickActiveSectionId(["missing-a", "missing-b"], {
        getElement: () => null
      })
    ).toBeNull();
  });

  it("keeps a tall section active while it spans the activation line", () => {
    const elements = new Map<string, { getBoundingClientRect: () => DOMRect }>([
      ["overview-section", { getBoundingClientRect: () => mockRect(-800, 700) }],
      ["career-companion-section", { getBoundingClientRect: () => mockRect(-100, 1400) }]
    ]);

    expect(
      pickActiveSectionId(["overview-section", "career-companion-section"], {
        offset: 16,
        activationLine: 200,
        getElement: (id) => (elements.get(id) as unknown as Element) ?? null
      })
    ).toBe("career-companion-section");
  });

  it("parses section ids from hashes", () => {
    expect(sectionIdFromHash("#github-section")).toBe("github-section");
    expect(sectionIdFromHash("")).toBeNull();
  });

  it("respects prefers-reduced-motion for scroll behavior", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("prefers-reduced-motion"),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn()
      }))
    });

    expect(prefersReducedMotion()).toBe(true);
    expect(resolveScrollBehavior("smooth")).toBe("auto");
  });

  it("scrolls to a section with the configured offset", () => {
    document.body.innerHTML = `<div id="github-section" style="height: 200px"></div>`;
    const target = document.getElementById("github-section");
    expect(target).not.toBeNull();
    vi.spyOn(target!, "getBoundingClientRect").mockReturnValue(mockRect(400));
    Object.defineProperty(window, "scrollY", { configurable: true, value: 100 });
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        media: "",
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn()
      }))
    });

    expect(scrollToSectionId("github-section", { offset: 16, behavior: "smooth" })).toBe(true);
    expect(scrollTo).toHaveBeenCalledWith({ top: 484, behavior: "smooth" });
  });
});

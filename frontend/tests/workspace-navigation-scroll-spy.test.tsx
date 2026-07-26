import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspaceNavigation, __testing } from "@/components/workspace-navigation";
import { useScrollSpy } from "@/hooks/use-scroll-spy";

const pathnameMock = vi.fn(() => "/");

vi.mock("next/navigation", () => ({
  usePathname: () => pathnameMock(),
  useRouter: () => ({ push: vi.fn() })
}));

vi.mock("@/lib/auth/hooks", () => ({
  useLogout: () => vi.fn()
}));

type ObserverInstance = {
  callback: IntersectionObserverCallback;
  observe: ReturnType<typeof vi.fn>;
  unobserve: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
};

let observers: ObserverInstance[] = [];

function mockIntersectionObserver() {
  observers = [];
  class MockIntersectionObserver {
    callback: IntersectionObserverCallback;
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
    root = null;
    rootMargin = "";
    thresholds = [];

    constructor(callback: IntersectionObserverCallback) {
      this.callback = callback;
      observers.push(this);
    }

    takeRecords(): IntersectionObserverEntry[] {
      return [];
    }
  }

  vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);
}

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

beforeEach(() => {
  pathnameMock.mockReturnValue("/");
  mockIntersectionObserver();
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
});

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("WorkspaceNavigation scroll awareness", () => {
  it("highlights Overview initially on the Overview route", () => {
    render(<WorkspaceNavigation role="candidate" email="candidate@example.com" />);

    const overview = screen.getAllByRole("link", { name: "Overview" })[0];
    expect(overview).toHaveAttribute("aria-current", "location");
    expect(screen.getAllByRole("link", { name: "GitHub" })[0]).not.toHaveAttribute("aria-current");
  });

  it("uses updated semantic section hashes for candidate anchors", () => {
    render(<WorkspaceNavigation role="candidate" />);

    const resume = screen.getAllByRole("link", { name: "Resume" })[0];
    const github = screen.getAllByRole("link", { name: "GitHub" })[0];
    expect(resume).toHaveAttribute("href", "/#resume-section");
    expect(github).toHaveAttribute("href", "/#github-section");
    expect(
      resume.compareDocumentPosition(github) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(screen.getAllByRole("link", { name: "Evidence" })[0]).toHaveAttribute("href", "/#evidence-section");
    expect(screen.getAllByRole("link", { name: "Career Companion" })[0]).toHaveAttribute(
      "href",
      "/#career-companion-section"
    );
  });

  it("keeps dedicated routes route-driven off Overview", () => {
    pathnameMock.mockReturnValue("/vacancies");
    render(<WorkspaceNavigation role="candidate" />);

    expect(screen.getAllByRole("link", { name: "Opportunities" })[0]).toHaveAttribute("aria-current", "page");
    expect(screen.getAllByRole("link", { name: "Overview" })[0]).not.toHaveAttribute("aria-current");
    expect(screen.getAllByRole("link", { name: "GitHub" })[0]).not.toHaveAttribute("aria-current");
  });

  it("uses aria-current=page for dedicated Profile route", () => {
    pathnameMock.mockReturnValue("/profile");
    render(<WorkspaceNavigation role="candidate" />);

    expect(screen.getAllByRole("link", { name: "Profile" })[0]).toHaveAttribute("aria-current", "page");
  });

  it("keeps employer destinations without Applicants", () => {
    render(<WorkspaceNavigation role="employer" />);

    expect(screen.getAllByRole("link", { name: "Vacancies" })[0]).toHaveAttribute("href", "/#employer-vacancies");
    expect(screen.queryByRole("link", { name: "Applicants" })).not.toBeInTheDocument();
    expect(screen.getByText("Menu").closest("summary")).toBeInTheDocument();
  });

  it("resolves active items from scroll section ids on Overview", () => {
    expect(
      __testing.isActiveNavItem(
        { href: "/vacancies", label: "Opportunities", kind: "route", sectionId: "opportunities-section" },
        "/",
        "opportunities-section"
      )
    ).toBe(true);

    expect(
      __testing.isActiveNavItem(
        { href: "/", label: "Overview", kind: "route", sectionId: "overview-section" },
        "/",
        "opportunities-section"
      )
    ).toBe(false);

    expect(
      __testing.isActiveNavItem(
        { href: "/vacancies", label: "Opportunities", kind: "route", sectionId: "opportunities-section" },
        "/vacancies",
        "opportunities-section"
      )
    ).toBe(true);

    expect(__testing.ariaCurrentFor(
      { href: "/#github-section", label: "GitHub", kind: "anchor", sectionId: "github-section" },
      true,
      true
    )).toBe("location");
  });

  it("smooth-scrolls to a current-page section on click", () => {
    document.body.innerHTML = `<div id="github-section"></div>`;
    const target = document.getElementById("github-section")!;
    vi.spyOn(target, "getBoundingClientRect").mockReturnValue(mockRect(500));
    Object.defineProperty(window, "scrollY", { configurable: true, value: 0 });
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
    const replaceState = vi.spyOn(window.history, "replaceState").mockImplementation(() => undefined);

    render(<WorkspaceNavigation role="candidate" />);
    fireEvent.click(screen.getAllByRole("link", { name: "GitHub" })[0]);

    expect(scrollTo).toHaveBeenCalled();
    expect(replaceState).toHaveBeenCalledWith(null, "", "/#github-section");
    expect(screen.getAllByRole("link", { name: "GitHub" })[0]).toHaveAttribute("aria-current", "location");
  });
});

describe("useScrollSpy", () => {
  it("updates the active section when observed geometry changes", async () => {
    document.body.innerHTML = `
      <div id="overview-section"></div>
      <div id="opportunities-section"></div>
      <div id="github-section"></div>
    `;

    const overview = document.getElementById("overview-section")!;
    const opportunities = document.getElementById("opportunities-section")!;
    const github = document.getElementById("github-section")!;

    vi.spyOn(overview, "getBoundingClientRect").mockReturnValue(mockRect(-20));
    vi.spyOn(opportunities, "getBoundingClientRect").mockReturnValue(mockRect(80));
    vi.spyOn(github, "getBoundingClientRect").mockReturnValue(mockRect(700));

    const { result, unmount } = renderHook(() =>
      useScrollSpy({
        sectionIds: ["overview-section", "opportunities-section", "github-section"],
        enabled: true
      })
    );

    expect(observers.length).toBe(1);
    expect(observers[0].observe).toHaveBeenCalledTimes(3);

    await act(async () => {
      observers[0].callback([], observers[0] as unknown as IntersectionObserver);
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)));
    });

    expect(result.current).toBe("opportunities-section");

    vi.spyOn(overview, "getBoundingClientRect").mockReturnValue(mockRect(-900));
    vi.spyOn(opportunities, "getBoundingClientRect").mockReturnValue(mockRect(-500));
    vi.spyOn(github, "getBoundingClientRect").mockReturnValue(mockRect(60));

    await act(async () => {
      observers[0].callback([], observers[0] as unknown as IntersectionObserver);
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)));
    });

    expect(result.current).toBe("github-section");

    vi.spyOn(overview, "getBoundingClientRect").mockReturnValue(mockRect(40));
    vi.spyOn(opportunities, "getBoundingClientRect").mockReturnValue(mockRect(500));
    vi.spyOn(github, "getBoundingClientRect").mockReturnValue(mockRect(1100));

    await act(async () => {
      observers[0].callback([], observers[0] as unknown as IntersectionObserver);
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)));
    });

    expect(result.current).toBe("overview-section");

    unmount();
    expect(observers[0].disconnect).toHaveBeenCalled();
  });

  it("ignores missing sections and honors a locked section during click scroll", async () => {
    document.body.innerHTML = `<div id="overview-section"></div><div id="github-section"></div>`;
    const overview = document.getElementById("overview-section")!;
    const github = document.getElementById("github-section")!;
    vi.spyOn(overview, "getBoundingClientRect").mockReturnValue(mockRect(20));
    vi.spyOn(github, "getBoundingClientRect").mockReturnValue(mockRect(700));

    const { result, rerender, unmount } = renderHook(
      ({ locked }) =>
        useScrollSpy({
          sectionIds: ["overview-section", "missing-section", "github-section"],
          enabled: true,
          lockedSectionId: locked
        }),
      { initialProps: { locked: "github-section" as string | null } }
    );

    expect(result.current).toBe("github-section");

    rerender({ locked: null });

    await act(async () => {
      observers[0].callback([], observers[0] as unknown as IntersectionObserver);
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)));
    });

    expect(result.current).toBe("overview-section");
    unmount();
  });

  it("does not observe when disabled on dedicated routes", () => {
    const { result, unmount } = renderHook(() =>
      useScrollSpy({
        sectionIds: ["overview-section"],
        enabled: false
      })
    );

    expect(result.current).toBeNull();
    expect(observers.length).toBe(0);
    unmount();
  });
});

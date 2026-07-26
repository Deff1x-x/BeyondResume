import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  EvidenceIntelligenceFlow,
  type EvidenceIntelligenceFlowState
} from "@/components/evidence-intelligence-flow";

function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    }))
  });
}

function renderFlow(state: EvidenceIntelligenceFlowState = "idle") {
  return render(<EvidenceIntelligenceFlow state={state} />);
}

describe("EvidenceIntelligenceFlow", () => {
  beforeEach(() => {
    mockMatchMedia(false);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("renders all four grounded steps", () => {
    renderFlow("idle");
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Verified Skills")).toBeInTheDocument();
    expect(screen.getByText("Candidate Match")).toBeInTheDocument();
    expect(screen.getByText("AI Insight")).toBeInTheDocument();
  });

  it("keeps deterministic steps complete while AI waits in idle", () => {
    const { container } = renderFlow("idle");
    const steps = container.querySelectorAll(".eif-step");
    expect(steps[0]).toHaveAttribute("data-status", "complete");
    expect(steps[1]).toHaveAttribute("data-status", "complete");
    expect(steps[2]).toHaveAttribute("data-status", "complete");
    expect(steps[3]).toHaveAttribute("data-status", "waiting");
    expect(screen.getByText("Waiting")).toBeInTheDocument();
  });

  it("marks AI Insight active while loading", () => {
    const { container } = renderFlow("loading");
    expect(container.querySelector('[data-step="ai"]')).toHaveAttribute(
      "data-status",
      "active"
    );
    expect(screen.getByText("Generating")).toBeInTheDocument();
    expect(container.querySelector('[data-step="match"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
  });

  it("marks AI Insight complete on success", () => {
    const { container } = renderFlow("success");
    expect(container.querySelector('[data-step="ai"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("keeps deterministic steps complete when AI is unavailable", () => {
    const { container } = renderFlow("error");
    expect(container.querySelector('[data-step="evidence"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
    expect(container.querySelector('[data-step="skills"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
    expect(container.querySelector('[data-step="match"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
    expect(container.querySelector('[data-step="ai"]')).toHaveAttribute(
      "data-status",
      "error"
    );
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(
      screen.getByText(/Deterministic steps remain complete/i)
    ).toBeInTheDocument();
  });

  it("exposes semantic status without relying on hover", () => {
    const { container } = renderFlow("loading");
    const group = container.querySelector(".eif");
    expect(group).toHaveAttribute("role", "group");
    expect(group).toHaveAttribute("data-state", "loading");
    expect(screen.getByText(/AI Insight is generating/i)).toBeInTheDocument();
    expect(container.querySelector(".eif-track")).toBeInTheDocument();
  });

  it("settles immediately under prefers-reduced-motion", () => {
    mockMatchMedia(true);
    const { container } = renderFlow("idle");
    expect(container.querySelector(".eif")).toHaveAttribute("data-phase", "settled");
    expect(screen.getByText("Evidence")).toBeVisible();
    expect(screen.getByText("AI Insight")).toBeVisible();
  });

  it("does not replay entrance animation when only state changes", async () => {
    const { container, rerender } = renderFlow("idle");
    expect(["playing", "pending", "settled"]).toContain(
      container.querySelector(".eif")?.getAttribute("data-phase")
    );

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    });
    expect(container.querySelector(".eif")).toHaveAttribute("data-phase", "settled");

    rerender(<EvidenceIntelligenceFlow state="loading" />);
    expect(container.querySelector(".eif")).toHaveAttribute("data-phase", "settled");
    expect(container.querySelector(".eif")).toHaveAttribute("data-state", "loading");

    rerender(<EvidenceIntelligenceFlow state="error" />);
    expect(container.querySelector(".eif")).toHaveAttribute("data-phase", "settled");
    expect(container.querySelector('[data-step="match"]')).toHaveAttribute(
      "data-status",
      "complete"
    );
  });

  it("hides decorative connectors from the accessibility tree", () => {
    const { container } = renderFlow("success");
    const connectors = container.querySelectorAll(".eif-connector");
    expect(connectors.length).toBe(3);
    connectors.forEach((node) => {
      expect(node).toHaveAttribute("aria-hidden", "true");
    });
  });
});

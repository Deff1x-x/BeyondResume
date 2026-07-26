/**
 * @vitest-environment jsdom
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

import { DemoEntryButton } from "@/components/demo-entry";
import { DemoModeBadge } from "@/components/demo-mode-badge";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh })
}));

vi.mock("@/lib/api/demo", () => ({
  getDemoStatus: vi.fn(async () => ({ enabled: true, roles: ["candidate", "employer"] })),
  startDemo: vi.fn(async () => ({ access_token: "demo-token", token_type: "bearer" })),
  resetDemo: vi.fn(async () => ({
    ok: true,
    role: "candidate",
    access_token: "reset-token",
    token_type: "bearer"
  }))
}));

vi.mock("@/lib/auth/hooks", () => ({
  currentUserQueryKey: ["me"],
  useCurrentUser: () => ({
    data: {
      id: "demo-id",
      email: "demo.candidate@beyondresume.dev",
      role: "candidate",
      status: "active"
    }
  })
}));

vi.mock("@/lib/auth/token", () => ({
  setAccessToken: vi.fn(),
  clearAccessToken: vi.fn(),
  getAccessToken: vi.fn(() => "token")
}));

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  push.mockReset();
  refresh.mockReset();
  sessionStorage.clear();

  if (typeof HTMLDialogElement !== "undefined") {
    HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
      this.setAttribute("open", "");
    };
    HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    };
  }
});

afterEach(cleanup);

describe("Demo Mode UI", () => {
  it("opens modal with candidate and employer choices", async () => {
    wrap(<DemoEntryButton />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Try Live Demo" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Try Live Demo" }));

    expect(screen.getByRole("heading", { name: "Choose a live demo" })).toBeInTheDocument();
    expect(screen.getByText("Candidate Demo")).toBeInTheDocument();
    expect(
      screen.getByText("Experience BeyondResume from a candidate's perspective.")
    ).toBeInTheDocument();
    expect(screen.getByText("Employer Demo")).toBeInTheDocument();
    expect(
      screen.getByText("See how recruiters discover and evaluate talent.")
    ).toBeInTheDocument();
  });

  it("starts candidate demo and navigates home", async () => {
    const { startDemo } = await import("@/lib/api/demo");
    wrap(<DemoEntryButton />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Try Live Demo" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Try Live Demo" }));
    fireEvent.click(screen.getByRole("button", { name: /Candidate Demo/i }));

    await waitFor(() => expect(startDemo).toHaveBeenCalledWith({ role: "candidate" }));
    expect(push).toHaveBeenCalledWith("/");
  });

  it("renders demo badge with restart and exit", async () => {
    wrap(<DemoModeBadge />);
    expect(await screen.findByText("Demo Mode")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Restart Demo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exit Demo" })).toBeInTheDocument();
  });

  it("restarts the demo and refreshes the workspace", async () => {
    const { resetDemo } = await import("@/lib/api/demo");
    wrap(<DemoModeBadge />);

    fireEvent.click(await screen.findByRole("button", { name: "Restart Demo" }));

    await waitFor(() => expect(resetDemo).toHaveBeenCalledOnce());
    expect(push).toHaveBeenCalledWith("/");
    expect(refresh).toHaveBeenCalledOnce();
  });

  it("exits the demo, clears auth, and returns to landing", async () => {
    const { clearAccessToken } = await import("@/lib/auth/token");
    wrap(<DemoModeBadge />);

    fireEvent.click(await screen.findByRole("button", { name: "Exit Demo" }));

    expect(clearAccessToken).toHaveBeenCalledOnce();
    expect(sessionStorage.getItem("beyondresume_demo_session")).toBeNull();
    expect(push).toHaveBeenCalledWith("/landing");
  });
});

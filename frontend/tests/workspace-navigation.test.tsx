import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceNavigation } from "@/components/workspace-navigation";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() })
}));

vi.mock("@/lib/auth/hooks", () => ({
  useLogout: () => vi.fn()
}));

afterEach(cleanup);

describe("WorkspaceNavigation", () => {
  it("keeps candidate routes and in-page evidence destinations distinct", () => {
    render(<WorkspaceNavigation role="candidate" email="candidate@example.com" />);

    expect(screen.getAllByRole("link", { name: "Overview" })[0]).toHaveAttribute("href", "/");
    expect(screen.getAllByRole("link", { name: "Skill Passport" })[0]).toHaveAttribute("href", "/skill-passport");
    expect(screen.getAllByRole("link", { name: "GitHub" })[0]).toHaveAttribute("href", "/#github-section-title");
    expect(screen.getAllByRole("link", { name: "Overview" })[0]).toHaveAttribute("aria-current", "page");
    expect(screen.getAllByRole("link", { name: "GitHub" })[0]).not.toHaveAttribute("aria-current");
  });

  it("shows only safe existing employer destinations and keeps mobile navigation operable", () => {
    render(<WorkspaceNavigation role="employer" />);

    expect(screen.getAllByRole("link", { name: "Vacancies" })[0]).toHaveAttribute("href", "/#employer-vacancies");
    expect(screen.getAllByRole("link", { name: "Matches" })[0]).toHaveAttribute("href", "/#top-matches-by-vacancy");
    expect(screen.queryByRole("link", { name: "AI Hiring Intelligence" })).not.toBeInTheDocument();
    expect(screen.getByText("Menu").closest("summary")).toBeInTheDocument();
  });
});

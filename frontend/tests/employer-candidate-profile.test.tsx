import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EmployerSkillPassport } from "@/features/match-details/employer-skill-passport";
import type { MatchDetailsMatch, MatchDetailsPassport } from "@/lib/api/types/employer";

const match: MatchDetailsMatch = {
  score: 91,
  required: { matched: ["Python"], missing: ["Redis"] },
  preferred: { matched: ["Docker"], missing: ["Kubernetes"] }
};

const passport: MatchDetailsPassport = {
  top_skills: ["Python", "Docker", "Additional skill"],
  skills: [
    {
      name: "Python",
      evidence_confidence: 0.87,
      evidence_count: 3,
      source_types: ["github_repository", "resume"]
    },
    {
      name: "Docker",
      evidence_confidence: 0,
      evidence_count: 1,
      source_types: ["github_repository"]
    },
    {
      name: "Additional skill",
      evidence_confidence: 0.5,
      evidence_count: 2,
      source_types: ["portfolio_source"]
    }
  ]
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("EmployerSkillPassport", () => {
  it("renders canonical per-skill confidence once, evidence counts, source labels, and vacancy relevance", () => {
    render(<EmployerSkillPassport passport={passport} match={match} onSelectSkill={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Skill Passport" })).toBeInTheDocument();
    expect(screen.getByText("87%")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getAllByText("Evidence confidence")).toHaveLength(3);
    expect(screen.getByText("3 evidence items")).toBeInTheDocument();
    expect(screen.getAllByText("GitHub")).toHaveLength(2);
    expect(screen.getByText("Resume")).toBeInTheDocument();
    expect(screen.getByText("Portfolio Source")).toBeInTheDocument();
    expect(screen.getByText("Required · Matched")).toBeInTheDocument();
    expect(screen.getByText("Preferred · Matched")).toBeInTheDocument();
    expect(screen.getAllByText("Additional skill")).toHaveLength(2);
    expect(screen.getByRole("progressbar", { name: "Python evidence confidence: 87 percent" })).toHaveAttribute("aria-valuenow", "87");
    expect(screen.getByRole("progressbar", { name: "Docker evidence confidence: 0 percent" })).toHaveAttribute("aria-valuenow", "0");
    expect(screen.queryByText("Redis evidence confidence")).not.toBeInTheDocument();
    expect(screen.queryByText("91% confidence")).not.toBeInTheDocument();
  });

  it("uses the existing evidence selection action without exposing editing controls", () => {
    const onSelectSkill = vi.fn();
    render(<EmployerSkillPassport passport={passport} match={match} onSelectSkill={onSelectSkill} />);

    fireEvent.click(screen.getAllByRole("button", { name: "View evidence" })[0]);
    expect(onSelectSkill).toHaveBeenCalledWith("Python");
    expect(screen.queryByRole("button", { name: /edit skill|remove skill|generate passport/i })).not.toBeInTheDocument();
  });

  it("uses names-only compatibility fallback when an older response omits skills", () => {
    render(<EmployerSkillPassport passport={{ top_skills: ["Python"] }} match={match} onSelectSkill={vi.fn()} />);

    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Confidence unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.queryByText("0%")).not.toBeInTheDocument();
  });

  it("treats an explicitly empty skills array as an empty Skill Passport", () => {
    render(<EmployerSkillPassport passport={{ top_skills: ["Legacy skill"], skills: [] }} match={match} onSelectSkill={vi.fn()} />);

    expect(screen.getByText("No evidence-backed skills are available for this candidate.")).toBeInTheDocument();
    expect(screen.queryByText("Legacy skill")).not.toBeInTheDocument();
  });
});

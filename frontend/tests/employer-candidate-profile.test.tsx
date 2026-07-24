import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EmployerSkillPassport } from "@/features/match-details/employer-skill-passport";
import { RoadmapCard } from "@/features/match-details/roadmap-card";
import { SkillsComparisonCard } from "@/features/match-details/skills-comparison-card";
import {
  getEvidenceCategoryLabel,
  getOwnershipStatusLabel,
  getVerificationBadgeTone,
  getVerificationStatusLabel
} from "@/lib/employer/explainability-labels";
import type {
  MatchDetailsMatch,
  MatchDetailsPassport,
  MatchSkillGroup
} from "@/lib/api/types/employer";

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
    expect(
      screen.getByRole("progressbar", { name: "Python evidence confidence: 87 percent" })
    ).toHaveAttribute("aria-valuenow", "87");
    expect(
      screen.getByRole("progressbar", { name: "Docker evidence confidence: 0 percent" })
    ).toHaveAttribute("aria-valuenow", "0");
    expect(screen.queryByText("Redis evidence confidence")).not.toBeInTheDocument();
    expect(screen.queryByText("91% confidence")).not.toBeInTheDocument();
  });

  it("uses the existing evidence selection action without exposing editing controls", () => {
    const onSelectSkill = vi.fn();
    render(<EmployerSkillPassport passport={passport} match={match} onSelectSkill={onSelectSkill} />);

    fireEvent.click(screen.getAllByRole("button", { name: "View evidence" })[0]);
    expect(onSelectSkill).toHaveBeenCalledWith("Python");
    expect(
      screen.queryByRole("button", { name: /edit skill|remove skill|generate passport/i })
    ).not.toBeInTheDocument();
  });

  it("uses names-only compatibility fallback when an older response omits skills", () => {
    render(
      <EmployerSkillPassport
        passport={{ top_skills: ["Python"] }}
        match={match}
        onSelectSkill={vi.fn()}
      />
    );

    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Confidence unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.queryByText("0%")).not.toBeInTheDocument();
  });

  it("treats an explicitly empty skills array as an empty Skill Passport", () => {
    render(
      <EmployerSkillPassport
        passport={{ top_skills: ["Legacy skill"], skills: [] }}
        match={match}
        onSelectSkill={vi.fn()}
      />
    );

    expect(
      screen.getByText("No evidence-backed skills are available for this candidate.")
    ).toBeInTheDocument();
    expect(screen.queryByText("Legacy skill")).not.toBeInTheDocument();
  });
});

describe("explainability-labels", () => {
  it("maps known evidence categories and hides unknown keys", () => {
    expect(getEvidenceCategoryLabel("resume_evidence")).toBe("Resume");
    expect(getEvidenceCategoryLabel("source_code_usage")).toBe("Source code usage");
    expect(getEvidenceCategoryLabel("source_import")).toBeNull();
    expect(getEvidenceCategoryLabel("dependency_manifest")).toBeNull();
  });

  it("maps verification and ownership without treating source_reachable as verified skill", () => {
    expect(getVerificationStatusLabel("source_reachable")).toBe("Source reachable");
    expect(getVerificationBadgeTone("source_reachable")).toBe("neutral");
    expect(getVerificationBadgeTone("issuer_verified")).toBe("success");
    expect(getVerificationStatusLabel("mystery_status")).toBeNull();
    expect(getOwnershipStatusLabel("verified")).toBe("Ownership verified");
    expect(getOwnershipStatusLabel("unverified")).toBe("Ownership unverified");
    expect(getOwnershipStatusLabel("ownership_confirmed")).toBeNull();
  });
});

describe("SkillsComparisonCard explainability", () => {
  const emptyCounts = new Map<string, number>();

  function renderComparison(props: {
    required: MatchSkillGroup;
    partial?: MatchSkillGroup;
    missing: MatchSkillGroup;
    evidenceCountBySkill?: Map<string, number>;
  }) {
    return render(
      <SkillsComparisonCard
        title="Skill comparison"
        headingId="skill-comparison-title"
        required={props.required}
        partial={props.partial ?? { matched: [], missing: [] }}
        missing={props.missing}
        evidenceCountBySkill={props.evidenceCountBySkill ?? emptyCounts}
        selectedSkill={null}
        onSelectSkill={vi.fn()}
      />
    );
  }

  it("keeps rendering when MatchSkillGroup has only string lists", () => {
    renderComparison({
      required: { matched: ["React"], missing: [] },
      missing: { matched: [], missing: ["Docker"] }
    });
    expect(screen.getByRole("button", { name: "View evidence for React" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View evidence for Docker" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /supporting evidence/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Not yet in Skill Passport")).not.toBeInTheDocument();
  });

  it("uses missing string lists as the primary missing rows", () => {
    renderComparison({
      required: { matched: [], missing: [] },
      missing: {
        matched: [],
        missing: ["Docker", "C#"],
        missing_details: [
          {
            skill_id: "docker-id",
            skill_name: "Docker",
            evidence_suggestions: [{ category: "resume_evidence" }]
          }
        ]
      }
    });
    expect(screen.getByRole("button", { name: "View evidence for Docker" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View evidence for C#" })).toBeInTheDocument();
    expect(screen.getByText("Not yet in Skill Passport")).toBeInTheDocument();
    expect(screen.queryByText("Ways this skill could be evidenced")).not.toBeNull();
  });

  it("expands matched supporting evidence with strength, trust statuses, and category labels", () => {
    renderComparison({
      required: {
        matched: ["React"],
        missing: [],
        matched_details: [
          {
            skill_id: "react-id",
            skill_name: "React",
            evidence: [
              {
                id: "ev-1",
                source_type: "github_repository",
                title: "GitHub repository: demo/frontend",
                verification_status: "source_reachable",
                ownership_status: "unverified",
                evidence_confidence: 0.82,
                signal_summaries: [
                  { category: "source_code_usage" },
                  { category: "source_import" },
                  { category: "test_usage" }
                ]
              }
            ]
          }
        ]
      },
      missing: { matched: [], missing: [] },
      evidenceCountBySkill: new Map([["React", 1]])
    });

    const expand = screen.getByRole("button", { name: "View supporting evidence" });
    expect(expand).toHaveAttribute("aria-expanded", "false");
    const regionId = expand.getAttribute("aria-controls");
    expect(regionId).toBeTruthy();

    fireEvent.click(expand);
    expect(expand).toHaveAttribute("aria-expanded", "true");
    expect(expand).toHaveAccessibleName("Hide supporting evidence");
    const region = document.getElementById(regionId!);
    expect(region).not.toBeNull();
    expect(within(region!).getByText("GitHub repository: demo/frontend")).toBeInTheDocument();
    expect(within(region!).getByText("GitHub")).toBeInTheDocument();
    expect(within(region!).getByText("Evidence strength:")).toBeInTheDocument();
    expect(within(region!).getByText("82%")).toBeInTheDocument();
    expect(within(region!).getByLabelText("Evidence strength 82 percent")).toBeInTheDocument();
    expect(within(region!).getByText("Source reachable")).toBeInTheDocument();
    expect(within(region!).getByText("Ownership unverified")).toBeInTheDocument();
    expect(within(region!).getByText("Evidence detected from")).toBeInTheDocument();
    expect(within(region!).getByText("Source code usage")).toBeInTheDocument();
    expect(within(region!).getByText("Tests")).toBeInTheDocument();
    expect(within(region!).queryByText("source_import")).not.toBeInTheDocument();
    expect(within(region!).queryByText("source_code_usage")).not.toBeInTheDocument();
    expect(screen.queryByText("Verified skill")).not.toBeInTheDocument();
    expect(screen.queryByText("Failed")).not.toBeInTheDocument();
  });

  it("hides empty summaries and null trust badges", () => {
    renderComparison({
      required: {
        matched: ["Python"],
        missing: [],
        matched_details: [
          {
            skill_id: "py-id",
            skill_name: "Python",
            evidence: [
              {
                id: "ev-resume",
                source_type: "resume",
                title: "Resume: ada.pdf",
                verification_status: null,
                ownership_status: null,
                evidence_confidence: 1,
                signal_summaries: []
              }
            ]
          }
        ]
      },
      missing: { matched: [], missing: [] }
    });

    fireEvent.click(screen.getByRole("button", { name: "View supporting evidence" }));
    expect(screen.getByText("Resume")).toBeInTheDocument();
    expect(screen.getByText("Evidence strength:")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.queryByText("Evidence detected from")).not.toBeInTheDocument();
    expect(screen.queryByText("Unverified")).not.toBeInTheDocument();
    expect(screen.queryByText("Ownership unverified")).not.toBeInTheDocument();
    expect(screen.queryByText("Failed")).not.toBeInTheDocument();
    expect(screen.queryByText("Invalid")).not.toBeInTheDocument();
  });

  it("hides unknown verification status keys and empty matched evidence containers", () => {
    renderComparison({
      required: {
        matched: ["Kotlin", "Swift"],
        missing: [],
        matched_details: [
          {
            skill_id: "kotlin-id",
            skill_name: "Kotlin",
            evidence: [
              {
                id: "ev-k",
                source_type: "github_repository",
                title: "Repo",
                verification_status: "future_unknown_status",
                ownership_status: "weird_ownership",
                evidence_confidence: 0.4,
                signal_summaries: [{ category: "future_unknown_category" }]
              }
            ]
          },
          {
            skill_id: "swift-id",
            skill_name: "Swift",
            evidence: []
          }
        ]
      },
      missing: { matched: [], missing: [] }
    });

    fireEvent.click(screen.getByRole("button", { name: "View supporting evidence" }));
    expect(screen.queryByText("future_unknown_status")).not.toBeInTheDocument();
    expect(screen.queryByText("weird_ownership")).not.toBeInTheDocument();
    expect(screen.queryByText("future_unknown_category")).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence detected from")).not.toBeInTheDocument();
    // Swift has empty evidence → no expand control; only Kotlin exposes one.
    expect(screen.getAllByRole("button", { name: /supporting evidence/i })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Hide supporting evidence" })).toBeInTheDocument();
  });

  it("renders missing suggestions with safe wording and hides unknown categories", () => {
    renderComparison({
      required: { matched: [], missing: [] },
      missing: {
        matched: [],
        missing: ["Docker"],
        missing_details: [
          {
            skill_id: "docker-id",
            skill_name: "Docker",
            evidence_suggestions: [
              { category: "resume_evidence" },
              { category: "container_configuration" },
              { category: "secret_internal_detector" }
            ]
          }
        ]
      }
    });

    expect(screen.getByText("Not yet in Skill Passport")).toBeInTheDocument();
    expect(screen.getByText("Ways this skill could be evidenced")).toBeInTheDocument();
    expect(screen.getByText("Resume")).toBeInTheDocument();
    expect(screen.getByText("Container configuration")).toBeInTheDocument();
    expect(screen.getByText(/not required actions/i)).toBeInTheDocument();
    expect(screen.queryByText("secret_internal_detector")).not.toBeInTheDocument();
    expect(screen.queryByText(/Upload|Add Docker|Provide|Complete|Must/i)).not.toBeInTheDocument();
  });

  it("does not show a suggestions block when categories are empty after filtering", () => {
    renderComparison({
      required: { matched: [], missing: [] },
      missing: {
        matched: [],
        missing: ["C#"],
        missing_details: [
          {
            skill_id: "csharp-id",
            skill_name: "C#",
            evidence_suggestions: [{ category: "unknown_only" }]
          }
        ]
      }
    });

    expect(screen.getByText("Not yet in Skill Passport")).toBeInTheDocument();
    expect(screen.queryByText("Ways this skill could be evidenced")).not.toBeInTheDocument();
    expect(screen.queryByText("unknown_only")).not.toBeInTheDocument();
  });

  it("keeps privacy-sensitive internal tokens out of the DOM", () => {
    renderComparison({
      required: {
        matched: ["React"],
        missing: [],
        matched_details: [
          {
            skill_id: "react-id",
            skill_name: "React",
            evidence: [
              {
                id: "ev-1",
                source_type: "github_repository",
                title: "Safe title",
                verification_status: "issuer_verified",
                ownership_status: "verified",
                evidence_confidence: 0.9,
                signal_summaries: [{ category: "project_dependencies" }]
              }
            ]
          }
        ]
      },
      missing: { matched: [], missing: [] }
    });
    fireEvent.click(screen.getByRole("button", { name: "View supporting evidence" }));
    const markup = document.body.textContent ?? "";
    for (const forbidden of [
      "source_import",
      "dependency_manifest",
      "rule_id",
      "matched_value",
      "secret.config.json"
    ]) {
      expect(markup).not.toContain(forbidden);
    }
    expect(screen.getByText("Issuer verified")).toBeInTheDocument();
    expect(screen.getByText("Ownership verified")).toBeInTheDocument();
    expect(screen.getByText("Project dependencies")).toBeInTheDocument();
  });

  it("isolates duplicate skill names across required and preferred groups", () => {
    renderComparison({
      required: {
        matched: ["React"],
        missing: [],
        matched_details: [
          {
            skill_id: "required-react-id",
            skill_name: "React",
            evidence: [
              {
                id: "required-ev",
                source_type: "resume",
                title: "Required React evidence",
                verification_status: null,
                ownership_status: null,
                evidence_confidence: 0.7,
                signal_summaries: [{ category: "resume_evidence" }]
              }
            ]
          }
        ]
      },
      partial: {
        matched: ["React"],
        missing: [],
        matched_details: [
          {
            skill_id: "preferred-react-id",
            skill_name: "React",
            evidence: [
              {
                id: "preferred-ev",
                source_type: "github_repository",
                title: "Preferred React evidence",
                verification_status: null,
                ownership_status: null,
                evidence_confidence: 0.9,
                signal_summaries: [{ category: "source_code_usage" }]
              }
            ]
          }
        ]
      },
      missing: { matched: [], missing: [] }
    });

    const expandButtons = screen.getAllByRole("button", { name: "View supporting evidence" });
    expect(expandButtons).toHaveLength(2);
    const firstControls = expandButtons[0].getAttribute("aria-controls");
    const secondControls = expandButtons[1].getAttribute("aria-controls");
    expect(firstControls).toBeTruthy();
    expect(secondControls).toBeTruthy();
    expect(firstControls).not.toEqual(secondControls);

    fireEvent.click(expandButtons[0]);
    expect(expandButtons[0]).toHaveAttribute("aria-expanded", "true");
    expect(expandButtons[1]).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByText("Required React evidence")).toBeInTheDocument();
    expect(screen.queryByText("Preferred React evidence")).not.toBeInTheDocument();

    fireEvent.click(expandButtons[1]);
    expect(expandButtons[1]).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Preferred React evidence")).toBeInTheDocument();
    expect(screen.getByText("Required React evidence")).toBeInTheDocument();
  });
});

describe("Roadmap separation from evidence suggestions", () => {
  it("does not render suggestion headings inside the roadmap section", () => {
    render(
      <RoadmapCard
        items={[
          {
            id: "roadmap-1",
            title: "Learn Docker",
            reason: "Strengthen preferred stack",
            priority: "medium",
            missing_skills: ["Docker"],
            related_skills: []
          }
        ]}
      />
    );
    const roadmap = screen.getByRole("heading", { name: "Roadmap" }).closest("[aria-labelledby]");
    expect(roadmap).not.toBeNull();
    expect(
      within(roadmap as HTMLElement).queryByText("Ways this skill could be evidenced")
    ).not.toBeInTheDocument();
    expect(within(roadmap as HTMLElement).queryByText("Not yet in Skill Passport")).not.toBeInTheDocument();
  });
});

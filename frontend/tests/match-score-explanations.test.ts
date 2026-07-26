/**
 * @vitest-environment jsdom
 */
import { describe, expect, it } from "vitest";

import { buildMatchScoreExplanations } from "@/lib/employer/match-score-explanations";
import type { VacancyMatch } from "@/lib/api/types/employer";

function match(partial: Partial<VacancyMatch> & Pick<VacancyMatch, "score">): VacancyMatch {
  return {
    candidate_id: "c1",
    candidate_name: "Alex Rivera",
    required: { matched: ["Python", "PostgreSQL"], missing: ["Docker"] },
    preferred: { matched: ["TypeScript"], missing: ["React", "Kubernetes"] },
    ...partial
  };
}

describe("buildMatchScoreExplanations", () => {
  it("explains coverage without inventing a score", () => {
    const lines = buildMatchScoreExplanations(match({ score: 85 }));
    expect(lines.some((line) => line.includes("2 of 3 required"))).toBe(true);
    expect(lines.some((line) => line.includes("Missing Docker"))).toBe(true);
    expect(lines.some((line) => line.includes("Preferred skill coverage: 1 of 3"))).toBe(true);
    expect(lines.join(" ")).not.toMatch(/\b100%\b/);
    expect(lines.join(" ")).not.toContain("85%");
  });

  it("stays deterministic for identical match payloads", () => {
    const a = buildMatchScoreExplanations(match({ score: 75 }));
    const b = buildMatchScoreExplanations(match({ score: 75 }));
    expect(a).toEqual(b);
  });
});

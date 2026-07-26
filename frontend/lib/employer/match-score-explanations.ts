import type { VacancyMatch } from "@/lib/api/types/employer";

/**
 * Concise, deterministic explanations derived from backend match breakdowns.
 * Does not invent or recalculate the Match Score.
 */
export function buildMatchScoreExplanations(match: VacancyMatch): string[] {
  const lines: string[] = [];
  const requiredTotal = match.required.matched.length + match.required.missing.length;
  const preferredTotal = match.preferred.matched.length + match.preferred.missing.length;

  if (requiredTotal > 0) {
    lines.push(
      `${match.required.matched.length} of ${requiredTotal} required skills matched`
    );
  }
  if (match.required.missing.length === 1) {
    lines.push(`Missing ${match.required.missing[0]}`);
  } else if (match.required.missing.length > 1) {
    lines.push(`Missing required: ${match.required.missing.slice(0, 3).join(", ")}`);
  }

  if (preferredTotal > 0) {
    lines.push(
      `Preferred skill coverage: ${match.preferred.matched.length} of ${preferredTotal}`
    );
  }

  if (match.required.matched.length >= 2) {
    lines.push(
      `Strong coverage for ${match.required.matched.slice(0, 2).join(" and ")}`
    );
  } else if (match.preferred.matched.length >= 2 && match.required.matched.length > 0) {
    lines.push(
      `Preferred strengths include ${match.preferred.matched.slice(0, 2).join(" and ")}`
    );
  }

  return lines.slice(0, 4);
}

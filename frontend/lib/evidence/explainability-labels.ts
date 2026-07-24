/** Shared presentation labels for evidence explainability (candidate and employer). */

const VERIFICATION_STATUS_LABELS: Readonly<Record<string, string>> = {
  unverified: "Unverified",
  source_reachable: "Source reachable",
  ownership_confirmed: "Ownership confirmed",
  issuer_verified: "Issuer verified",
  platform_assessed: "Platform assessed",
  disputed: "Disputed",
  invalidated: "Invalidated"
};

const OWNERSHIP_STATUS_LABELS: Readonly<Record<string, string>> = {
  verified: "Ownership verified",
  unverified: "Ownership unverified"
};

const SOURCE_TYPE_LABELS: Readonly<Record<string, string>> = {
  resume: "Resume",
  github_repository: "GitHub"
};

export const EVIDENCE_STRENGTH_LABEL = "Evidence strength";

export type ExplainabilityBadgeTone = "neutral" | "success" | "danger";

/** @deprecated Prefer ExplainabilityBadgeTone; kept for employer import compatibility. */
export type VerificationBadgeTone = ExplainabilityBadgeTone;

export function getVerificationStatusLabel(status: string): string | null {
  return VERIFICATION_STATUS_LABELS[status] ?? null;
}

export function getOwnershipStatusLabel(status: string): string | null {
  return OWNERSHIP_STATUS_LABELS[status] ?? null;
}

export function getEvidenceSourceTypeLabel(sourceType: string): string {
  return SOURCE_TYPE_LABELS[sourceType] ?? "Evidence";
}

/**
 * Safe badge tone for verification_status.
 * source_reachable is never treated as skill/ownership verification.
 */
export function getVerificationBadgeTone(status: string): ExplainabilityBadgeTone {
  if (status === "issuer_verified") {
    return "success";
  }
  if (status === "disputed" || status === "invalidated") {
    return "danger";
  }
  return "neutral";
}

/** Ownership badges stay informational; never imply verification success. */
export function getOwnershipBadgeTone(status: string): ExplainabilityBadgeTone {
  void status;
  return "neutral";
}

/**
 * Formats backend evidence_confidence ∈ [0, 1] as a whole-number percent.
 * Does not clamp, classify strength, or map to proficiency.
 */
export function formatEvidenceStrengthPercent(evidenceConfidence: number): number {
  return Math.round(evidenceConfidence * 100);
}

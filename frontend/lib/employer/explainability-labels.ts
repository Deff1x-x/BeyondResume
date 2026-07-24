/** Centralized employer-safe labels for explainable matching UI. */

const EVIDENCE_CATEGORY_LABELS: Readonly<Record<string, string>> = {
  resume_evidence: "Resume",
  project_dependencies: "Project dependencies",
  source_code_usage: "Source code usage",
  test_usage: "Tests",
  application_configuration: "Application configuration",
  container_configuration: "Container configuration",
  ci_cd_configuration: "CI/CD configuration"
};

const VERIFICATION_STATUS_LABELS: Readonly<Record<string, string>> = {
  unverified: "Unverified",
  source_reachable: "Source reachable",
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

export function getEvidenceCategoryLabel(category: string): string | null {
  return EVIDENCE_CATEGORY_LABELS[category] ?? null;
}

export function getVerificationStatusLabel(status: string): string | null {
  return VERIFICATION_STATUS_LABELS[status] ?? null;
}

export function getOwnershipStatusLabel(status: string): string | null {
  return OWNERSHIP_STATUS_LABELS[status] ?? null;
}

export function getEvidenceSourceTypeLabel(sourceType: string): string {
  return SOURCE_TYPE_LABELS[sourceType] ?? "Evidence";
}

export type VerificationBadgeTone = "neutral" | "success" | "danger";

/** Safe badge tone: source_reachable is never treated as skill/ownership verification. */
export function getVerificationBadgeTone(status: string): VerificationBadgeTone {
  if (status === "issuer_verified") {
    return "success";
  }
  if (status === "disputed" || status === "invalidated") {
    return "danger";
  }
  return "neutral";
}

export function knownEvidenceCategoryLabels(categories: Iterable<string>): string[] {
  const labels: string[] = [];
  const seen = new Set<string>();
  for (const category of categories) {
    const label = getEvidenceCategoryLabel(category);
    if (label === null || seen.has(label)) {
      continue;
    }
    seen.add(label);
    labels.push(label);
  }
  return labels;
}

/** Employer-specific evidence category labels plus shared explainability helpers. */

export {
  EVIDENCE_STRENGTH_LABEL,
  formatEvidenceStrengthPercent,
  getEvidenceSourceTypeLabel,
  getOwnershipBadgeTone,
  getOwnershipStatusLabel,
  getVerificationBadgeTone,
  getVerificationStatusLabel,
  type ExplainabilityBadgeTone,
  type VerificationBadgeTone
} from "@/lib/evidence/explainability-labels";

const EVIDENCE_CATEGORY_LABELS: Readonly<Record<string, string>> = {
  resume_evidence: "Resume",
  project_dependencies: "Project dependencies",
  source_code_usage: "Source code usage",
  test_usage: "Tests",
  application_configuration: "Application configuration",
  container_configuration: "Container configuration",
  ci_cd_configuration: "CI/CD configuration"
};

export function getEvidenceCategoryLabel(category: string): string | null {
  return EVIDENCE_CATEGORY_LABELS[category] ?? null;
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

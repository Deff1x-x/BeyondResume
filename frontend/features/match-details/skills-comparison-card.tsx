"use client";

import { useId, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  getEvidenceSourceTypeLabel,
  getOwnershipStatusLabel,
  getVerificationBadgeTone,
  getVerificationStatusLabel,
  knownEvidenceCategoryLabels
} from "@/lib/employer/explainability-labels";
import type {
  MatchedSkillDetails,
  MatchedSkillEvidence,
  MatchSkillGroup,
  MissingSkillDetails
} from "@/lib/api/types/employer";

type SkillRow = {
  skill: string;
  status: "matched" | "partial" | "missing";
};

type SkillsComparisonCardProps = Readonly<{
  title: string;
  headingId: string;
  required: MatchSkillGroup;
  partial: MatchSkillGroup;
  missing: MatchSkillGroup;
  evidenceCountBySkill: Map<string, number>;
  selectedSkill: string | null;
  onSelectSkill: (skill: string) => void;
}>;

function statusBadge(status: SkillRow["status"]) {
  if (status === "matched") {
    return <Badge variant="success">Matched</Badge>;
  }
  if (status === "partial") {
    return <Badge variant="primary">Partially matched</Badge>;
  }
  return <Badge variant="neutral">Missing</Badge>;
}

function indexBySkillName<T extends { skill_name: string }>(
  items: T[] | undefined
): Map<string, T> {
  const map = new Map<string, T>();
  for (const item of items ?? []) {
    map.set(item.skill_name, item);
  }
  return map;
}

function evidenceStrengthPercent(value: number): number {
  return Math.round(value * 100);
}

function regionSuffix(skill: string): string {
  return skill.replace(/[^a-zA-Z0-9_-]+/g, "-");
}

function SignalCategoryChips({
  categories,
  heading
}: Readonly<{ categories: string[]; heading: string }>) {
  const labels = knownEvidenceCategoryLabels(categories);
  if (labels.length === 0) {
    return null;
  }
  return (
    <div className="mt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-secondary">{heading}</p>
      <ul className="mt-2 flex flex-wrap gap-2" aria-label={heading}>
        {labels.map((label) => (
          <li key={label}>
            <Badge variant="neutral">{label}</Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SupportingEvidenceList({
  evidence,
  listId
}: Readonly<{ evidence: MatchedSkillEvidence[]; listId: string }>) {
  if (evidence.length === 0) {
    return null;
  }
  return (
    <ul id={listId} className="mt-3 space-y-3">
      {evidence.map((item) => {
        const strength = evidenceStrengthPercent(item.evidence_confidence);
        const verificationLabel =
          item.verification_status === null
            ? null
            : getVerificationStatusLabel(item.verification_status);
        const ownershipLabel =
          item.ownership_status === null
            ? null
            : getOwnershipStatusLabel(item.ownership_status);
        const summaryCategories = (item.signal_summaries ?? []).map((entry) => entry.category);
        return (
          <li
            key={item.id}
            className="rounded-lg border border-border bg-background px-3 py-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="neutral">{getEvidenceSourceTypeLabel(item.source_type)}</Badge>
              <p className="min-w-0 break-words text-sm font-medium text-ink">
                {item.title?.trim() || "Untitled evidence"}
              </p>
            </div>
            <p
              className="mt-2 text-sm text-secondary"
              aria-label={`Evidence strength ${strength} percent`}
            >
              Evidence strength:{" "}
              <span className="font-medium tabular-nums text-ink">{strength}%</span>
            </p>
            {(verificationLabel || ownershipLabel) && (
              <div className="mt-2 flex flex-wrap gap-2">
                {verificationLabel && item.verification_status ? (
                  <Badge variant={getVerificationBadgeTone(item.verification_status)}>
                    {verificationLabel}
                  </Badge>
                ) : null}
                {ownershipLabel ? <Badge variant="neutral">{ownershipLabel}</Badge> : null}
              </div>
            )}
            <SignalCategoryChips
              categories={summaryCategories}
              heading="Evidence detected from"
            />
          </li>
        );
      })}
    </ul>
  );
}

function MatchedExplainability({
  detail,
  controlId,
  regionId
}: Readonly<{ detail: MatchedSkillDetails; controlId: string; regionId: string }>) {
  const [expanded, setExpanded] = useState(false);
  if (detail.evidence.length === 0) {
    return null;
  }
  return (
    <div className="mt-3">
      <Button
        id={controlId}
        type="button"
        size="sm"
        variant="ghost"
        aria-expanded={expanded}
        aria-controls={regionId}
        onClick={() => setExpanded((value) => !value)}
      >
        {expanded ? "Hide supporting evidence" : "View supporting evidence"}
      </Button>
      {expanded ? (
        <div id={regionId} role="region" aria-labelledby={controlId} className="mt-2">
          <p className="text-xs font-medium uppercase tracking-wide text-secondary">
            Supporting evidence
          </p>
          <SupportingEvidenceList evidence={detail.evidence} listId={`${regionId}-list`} />
        </div>
      ) : null}
    </div>
  );
}

function MissingExplainability({ detail }: Readonly<{ detail: MissingSkillDetails }>) {
  const categories = detail.evidence_suggestions.map((item) => item.category);
  const labels = knownEvidenceCategoryLabels(categories);
  if (labels.length === 0) {
    return (
      <p className="mt-3 text-sm text-secondary">Not yet in Skill Passport</p>
    );
  }
  return (
    <div className="mt-3 space-y-2">
      <p className="text-sm font-medium text-ink">Not yet in Skill Passport</p>
      <SignalCategoryChips
        categories={categories}
        heading="Ways this skill could be evidenced"
      />
      <p className="text-xs leading-5 text-secondary">
        These are evidence categories the current system can recognize, not required actions.
      </p>
    </div>
  );
}

export function SkillsComparisonCard({
  title,
  headingId,
  required,
  partial,
  missing,
  evidenceCountBySkill,
  selectedSkill,
  onSelectSkill
}: SkillsComparisonCardProps) {
  const baseId = useId();
  const requiredMatchedDetailsByName = useMemo(
    () => indexBySkillName(required.matched_details),
    [required.matched_details]
  );
  const preferredMatchedDetailsByName = useMemo(
    () => indexBySkillName(partial.matched_details),
    [partial.matched_details]
  );
  const missingDetailsByName = useMemo(
    () => indexBySkillName(missing.missing_details),
    [missing.missing_details]
  );

  const rows: SkillRow[] = [
    ...required.matched.map((skill) => ({ skill, status: "matched" as const })),
    ...partial.matched.map((skill) => ({ skill, status: "partial" as const })),
    ...missing.missing.map((skill) => ({ skill, status: "missing" as const }))
  ];

  return (
    <Card aria-labelledby={headingId}>
      <CardContent className="p-5 sm:p-6">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">
            Match breakdown
          </p>
          <h2 id={headingId} className="mt-2 text-xl font-semibold tracking-tight text-ink">
            {title}
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Required matches, preferred-skill alignment, and gaps reported by the existing match
            engine.
          </p>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <GroupSummary label="Matched" count={required.matched.length} variant="success" />
          <GroupSummary
            label="Partially matched"
            count={partial.matched.length}
            variant="primary"
          />
          <GroupSummary label="Missing" count={missing.missing.length} variant="neutral" />
        </div>
        {rows.length === 0 ? (
          <p className="mt-6 text-sm text-secondary">
            This vacancy has no skill comparison data yet.
          </p>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[40rem] border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr className="text-secondary">
                  <th scope="col" className="border-b border-border px-3 py-3 font-medium">
                    Required skill
                  </th>
                  <th scope="col" className="border-b border-border px-3 py-3 font-medium">
                    Candidate skill
                  </th>
                  <th scope="col" className="border-b border-border px-3 py-3 font-medium">
                    Evidence
                  </th>
                  <th scope="col" className="border-b border-border px-3 py-3 font-medium">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const evidenceCount = evidenceCountBySkill.get(row.skill) ?? 0;
                  const matchedDetail =
                    row.status === "matched"
                      ? requiredMatchedDetailsByName.get(row.skill)
                      : row.status === "partial"
                        ? preferredMatchedDetailsByName.get(row.skill)
                        : undefined;
                  const missingDetail =
                    row.status === "missing" ? missingDetailsByName.get(row.skill) : undefined;
                  // Group-scope ids so duplicate canonical names across required/preferred never collide.
                  const controlId = `${baseId}-control-${row.status}-${regionSuffix(row.skill)}`;
                  const regionId = `${baseId}-region-${row.status}-${regionSuffix(row.skill)}`;
                  return (
                    <tr
                      key={`${row.status}-${row.skill}`}
                      className={selectedSkill === row.skill ? "bg-primary/5" : undefined}
                    >
                      <td className="border-b border-border px-3 py-4 align-top font-medium text-ink">
                        <button
                          type="button"
                          className="text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                          onClick={() => onSelectSkill(row.skill)}
                          aria-label={`View evidence for ${row.skill}`}
                        >
                          {row.skill}
                        </button>
                        {matchedDetail ? (
                          <MatchedExplainability
                            detail={matchedDetail}
                            controlId={controlId}
                            regionId={regionId}
                          />
                        ) : null}
                        {missingDetail ? <MissingExplainability detail={missingDetail} /> : null}
                      </td>
                      <td className="border-b border-border px-3 py-4 align-top text-secondary">
                        {row.status === "missing" ? "—" : row.skill}
                      </td>
                      <td className="border-b border-border px-3 py-4 align-top text-secondary">
                        {evidenceCount > 0
                          ? `${evidenceCount} ${evidenceCount === 1 ? "source" : "sources"}`
                          : "No linked evidence"}
                      </td>
                      <td className="border-b border-border px-3 py-4 align-top">
                        {statusBadge(row.status)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function GroupSummary({
  label,
  count,
  variant
}: Readonly<{
  label: string;
  count: number;
  variant: "success" | "primary" | "neutral";
}>) {
  return (
    <div className="rounded-xl border border-border bg-surface/70 p-3">
      <Badge variant={variant}>{label}</Badge>
      <p className="mt-2 text-xl font-semibold tabular-nums text-ink">{count}</p>
    </div>
  );
}

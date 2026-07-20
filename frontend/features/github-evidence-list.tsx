"use client";

import { useState } from "react";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonListRow } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/error";
import type { EvidenceResponse } from "@/lib/api/types/github";
import { useGitHubRepositoryEvidenceQuery } from "@/lib/github/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "Evidence could not be loaded. Please try again.";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function evidenceTypeLabel(sourceType: string): string {
  if (sourceType === "github_repository") {
    return "GitHub repository";
  }

  return sourceType.replaceAll("_", " ");
}

function evidenceConfidencePercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function strengthScorePercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function EvidenceCard({ evidence }: Readonly<{ evidence: EvidenceResponse }>) {
  const [expanded, setExpanded] = useState(false);

  const title = evidence.title ?? evidence.source_reference ?? "Evidence";
  const isLinkSource = evidence.source_reference?.startsWith("https://") ?? false;

  return (
    <li>
      <Card className="bg-surface">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 space-y-2">
              <p className="break-words text-sm font-medium text-ink">{title}</p>
              <Badge variant="neutral">{evidenceTypeLabel(evidence.source_type)}</Badge>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setExpanded((open) => !open)}
              aria-expanded={expanded}
            >
              {expanded ? "Hide details" : "Details"}
            </Button>
          </div>

          {evidence.description ? (
            <p className={`mt-3 text-sm text-secondary ${expanded ? "" : "line-clamp-2"}`}>
              {evidence.description}
            </p>
          ) : (
            <p className="mt-3 text-sm text-secondary">No description available.</p>
          )}

          {evidence.source_reference ? (
            <p className="mt-3 break-all text-sm text-secondary">
              Source:{" "}
              {isLinkSource ? (
                <a
                  href={evidence.source_reference}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-primary underline-offset-2 hover:underline"
                >
                  {evidence.source_reference}
                </a>
              ) : (
                <span className="font-medium text-ink">{evidence.source_reference}</span>
              )}
            </p>
          ) : null}

          <div className="mt-3">
            <p className="text-sm font-medium text-ink">Skills</p>
            {evidence.skills.length === 0 ? (
              <p className="mt-1 text-sm text-secondary">
                No skills are linked to this evidence yet.
              </p>
            ) : (
              <ul className="mt-2 flex flex-wrap gap-2" aria-label="Evidence skills">
                {evidence.skills.map((skill) => (
                  <li key={`${skill.name}-${skill.extraction_method}`} className="min-w-0 max-w-full">
                    <Badge
                      variant="success"
                      title={`${skill.name} · ${evidenceConfidencePercent(skill.evidence_confidence)}`}
                    >
                      {skill.name}
                      <span className="ml-1.5 text-secondary">
                        {evidenceConfidencePercent(skill.evidence_confidence)}
                      </span>
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {expanded ? (
            <dl className="mt-4 grid gap-x-6 gap-y-2 border-t border-border pt-4 text-sm sm:grid-cols-2">
              {evidence.observed_at ? (
                <div>
                  <dt className="text-secondary">Observed</dt>
                  <dd className="font-medium text-ink">{formatDate(evidence.observed_at)}</dd>
                </div>
              ) : null}
              {evidence.verification_status ? (
                <div>
                  <dt className="text-secondary">Verification</dt>
                  <dd className="mt-1">
                    <StatusBadge status={evidence.verification_status} />
                  </dd>
                </div>
              ) : null}
              {evidence.ownership_status ? (
                <div>
                  <dt className="text-secondary">Ownership</dt>
                  <dd className="mt-1">
                    <StatusBadge status={evidence.ownership_status} />
                  </dd>
                </div>
              ) : null}
              {evidence.strength_score !== null ? (
                <div>
                  <dt className="text-secondary">Strength score</dt>
                  <dd className="font-medium text-ink">
                    {strengthScorePercent(evidence.strength_score)}
                  </dd>
                </div>
              ) : null}
              {evidence.skills.length > 0 ? (
                <div className="sm:col-span-2">
                  <dt className="text-secondary">Skill extraction</dt>
                  <dd className="mt-1 space-y-1">
                    {evidence.skills.map((skill) => (
                      <p key={`${skill.name}-${skill.extraction_method}`} className="text-ink">
                        {skill.name}
                        <span className="text-secondary">
                          {" "}
                          · {skill.category} · {skill.extraction_method} · Evidence
                          confidence {evidenceConfidencePercent(skill.evidence_confidence)}
                        </span>
                      </p>
                    ))}
                  </dd>
                </div>
              ) : null}
            </dl>
          ) : null}
        </CardContent>
      </Card>
    </li>
  );
}

export function GitHubEvidenceList({ repositoryId }: Readonly<{ repositoryId: string }>) {
  const evidenceQuery = useGitHubRepositoryEvidenceQuery(repositoryId, true);

  if (evidenceQuery.isLoading) {
    return (
      <ul className="space-y-3" aria-hidden="true">
        <li>
          <SkeletonListRow />
        </li>
      </ul>
    );
  }

  if (evidenceQuery.isError) {
    return (
      <EmptyState
        role="alert"
        title="Could not load evidence"
        description={errorMessage(evidenceQuery.error)}
        primaryAction={
          <Button type="button" variant="secondary" onClick={() => void evidenceQuery.refetch()}>
            Try again
          </Button>
        }
      />
    );
  }

  const evidence = evidenceQuery.data ?? [];
  if (evidence.length === 0) {
    return (
      <EmptyState
        title="No evidence yet"
        description="No evidence has been collected for this repository yet. Run an analysis to generate evidence."
        className="bg-background py-6"
      />
    );
  }

  return (
    <ul className="space-y-3">
      {evidence.map((unit) => (
        <EvidenceCard key={unit.id} evidence={unit} />
      ))}
    </ul>
  );
}

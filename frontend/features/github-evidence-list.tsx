"use client";

import { useState } from "react";

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
    <li className="rounded-card border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">{title}</p>
          <p className="mt-1 text-sm text-secondary">
            Type:{" "}
            <span className="font-medium text-ink">
              {evidenceTypeLabel(evidence.source_type)}
            </span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          className="min-h-control rounded-button border border-border bg-background px-4 text-sm font-medium text-ink"
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Details"}
        </button>
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
          <ul className="mt-2 space-y-1">
            {evidence.skills.map((skill) => (
              <li
                key={`${skill.name}-${skill.extraction_method}`}
                className="text-sm text-ink"
              >
                <span aria-hidden="true" className="mr-2 text-success">
                  ✓
                </span>
                {skill.name}
                <span className="ml-2 text-secondary">
                  {evidenceConfidencePercent(skill.evidence_confidence)}
                </span>
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
              <dd className="font-medium text-ink">
                {evidence.verification_status.replaceAll("_", " ")}
              </dd>
            </div>
          ) : null}
          {evidence.ownership_status ? (
            <div>
              <dt className="text-secondary">Ownership</dt>
              <dd className="font-medium text-ink">
                {evidence.ownership_status.replaceAll("_", " ")}
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
    </li>
  );
}

export function GitHubEvidenceList({ repositoryId }: Readonly<{ repositoryId: string }>) {
  const evidenceQuery = useGitHubRepositoryEvidenceQuery(repositoryId, true);

  if (evidenceQuery.isLoading) {
    return (
      <p className="text-sm text-secondary" role="status">
        Loading evidence…
      </p>
    );
  }

  if (evidenceQuery.isError) {
    return (
      <div>
        <p className="text-sm text-danger" role="alert">
          {errorMessage(evidenceQuery.error)}
        </p>
        <button
          type="button"
          onClick={() => void evidenceQuery.refetch()}
          className="mt-3 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Try again
        </button>
      </div>
    );
  }

  const evidence = evidenceQuery.data ?? [];
  if (evidence.length === 0) {
    return (
      <p className="text-sm text-secondary">
        No evidence has been collected for this repository yet. Run an analysis to
        generate evidence.
      </p>
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

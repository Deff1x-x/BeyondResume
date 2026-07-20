"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/icon";
import { ApiClientError } from "@/lib/api/error";
import type { SkillPassportSkill } from "@/lib/api/types/skill-passport";
import { useSkillPassportQuery } from "@/lib/skill-passport/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The skill passport could not be loaded. Please try again.";
}

function evidenceConfidencePercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function evidenceCountLabel(count: number): string {
  return count === 1 ? "1 evidence item" : `${count} evidence items`;
}

function sourceTypeLabel(sourceType: string): string {
  if (sourceType === "github_repository") {
    return "GitHub repository";
  }

  return sourceType.replaceAll("_", " ");
}

function SkillCard({ skill }: Readonly<{ skill: SkillPassportSkill }>) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li className="rounded-card border border-border bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">{skill.name}</p>
          <p className="mt-1 text-sm text-secondary">{skill.category}</p>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          className="min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Details"}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-secondary">
        <span>
          Evidence confidence:{" "}
          <span className="font-medium text-ink">
            {evidenceConfidencePercent(skill.evidence_confidence)}
          </span>
        </span>
        <span>
          Confirmed by{" "}
          <span className="font-medium text-ink">{evidenceCountLabel(skill.evidence_count)}</span>
        </span>
      </div>

      {expanded ? (
        <ul className="mt-4 space-y-3 border-t border-border pt-4">
          {skill.evidence.map((evidence) => (
            <li key={evidence.id} className="rounded-card border border-border bg-surface p-3">
              <p className="break-words text-sm font-medium text-ink">
                {evidence.title ?? evidence.source_reference ?? "Evidence"}
              </p>
              <p className="mt-1 text-sm text-secondary">
                {sourceTypeLabel(evidence.source_type)} · Evidence confidence{" "}
                {evidenceConfidencePercent(evidence.evidence_confidence)}
              </p>
              {evidence.source_reference ? (
                <p className="mt-1 break-all text-sm text-secondary">
                  Source:{" "}
                  {evidence.source_reference.startsWith("https://") ? (
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
              {evidence.description ? (
                <p className="mt-2 text-sm text-secondary">{evidence.description}</p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function SkillPassportSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const passportQuery = useSkillPassportQuery(enabled);

  if (!enabled) {
    return (
      <section
        className="section-panel lg:col-span-2"
        aria-labelledby="skill-passport-section-title"
      >
        <h2 id="skill-passport-section-title" className="flex items-center gap-3 text-xl font-semibold tracking-tight text-ink"><span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary"><Icon name="passport" className="h-[18px] w-[18px]" /></span>Skill Passport</h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          The skill passport is available only to candidate accounts.
        </p>
      </section>
    );
  }

  const passport = passportQuery.data;

  return (
    <section
      className="section-panel lg:col-span-2"
      aria-labelledby="skill-passport-section-title"
    >
      <h2 id="skill-passport-section-title" className="flex items-center gap-3 text-xl font-semibold tracking-tight text-ink"><span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary"><Icon name="passport" className="h-[18px] w-[18px]" /></span>Skill Passport</h2>
      <p className="mt-2 text-sm text-secondary">
        An aggregated view of your skills based on collected evidence.
      </p>

      <div className="mt-6">
        {passportQuery.isLoading ? (
          <p className="text-sm text-secondary" role="status">
            Loading skill passport…
          </p>
        ) : null}

        {passportQuery.isError ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(passportQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void passportQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Try again
            </button>
          </div>
        ) : null}

        {passport && passport.skills.length === 0 ? (
          <p className="text-sm text-secondary">
            No skills have been confirmed yet. Connect and analyze a GitHub repository to
            collect evidence of your skills.
          </p>
        ) : null}

        {passport && passport.skills.length > 0 ? (
          <>
            <p className="text-sm text-secondary">
              <span className="font-medium text-ink">{passport.total_skills}</span> skills
              confirmed by{" "}
              <span className="font-medium text-ink">{passport.total_evidence}</span>{" "}
              evidence {passport.total_evidence === 1 ? "item" : "items"}.
            </p>
            <ul className="mt-4 space-y-3">
              {passport.skills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} />
              ))}
            </ul>
          </>
        ) : null}
      </div>
    </section>
  );
}

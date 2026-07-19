"use client";

import { useDeferredValue, useMemo, useState } from "react";

import { ApiClientError } from "@/lib/api/error";
import { useEvidenceHubQuery } from "@/lib/evidence/hooks";

import { EvidenceEmptyState } from "./evidence-empty-state";
import { EvidenceList } from "./evidence-list";
import { EvidenceSkeleton } from "./evidence-skeleton";
import { EvidenceToolbar, type SourceFilter } from "./evidence-toolbar";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Evidence could not be loaded. Please try again.";
}

export function EvidenceHubSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const [search, setSearch] = useState("");
  const [skill, setSkill] = useState("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");

  const deferredSearch = useDeferredValue(search.trim());
  const deferredSkill = useDeferredValue(skill.trim());

  const queryParams = useMemo(
    () => ({
      search: deferredSearch || undefined,
      skill: deferredSkill || undefined,
      source_type: sourceFilter === "all" ? undefined : sourceFilter,
      limit: 20,
      offset: 0
    }),
    [deferredSearch, deferredSkill, sourceFilter]
  );

  const hasFilters =
    Boolean(deferredSearch) || Boolean(deferredSkill) || sourceFilter !== "all";

  const evidenceQuery = useEvidenceHubQuery(queryParams, enabled);

  function clearFilters() {
    setSearch("");
    setSkill("");
    setSourceFilter("all");
  }

  if (!enabled) {
    return null;
  }

  return (
    <section
      id="evidence-hub"
      className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
      aria-labelledby="evidence-hub-section-title"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 id="evidence-hub-section-title" className="text-xl font-semibold text-ink">
            Evidence
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            All confirmations of experience and skills from connected sources.
          </p>
        </div>
        <div className="shrink-0 text-sm text-secondary sm:text-right">
          <p>
            <span className="font-medium text-ink">
              {evidenceQuery.data?.total ?? "—"}
            </span>{" "}
            evidence
          </p>
          <p className="mt-1">
            Source:{" "}
            <span className="font-medium text-ink">
              {sourceFilter === "all"
                ? "All"
                : sourceFilter === "github"
                  ? "GitHub"
                  : "Resume"}
            </span>
          </p>
        </div>
      </div>

      <div className="mt-6">
        <EvidenceToolbar
          search={search}
          sourceFilter={sourceFilter}
          skill={skill}
          onSearchChange={setSearch}
          onSourceFilterChange={setSourceFilter}
          onSkillChange={setSkill}
        />
      </div>

      <div className="mt-4" aria-live="polite">
        {evidenceQuery.isLoading ? <EvidenceSkeleton /> : null}

        {evidenceQuery.isError ? (
          <EvidenceEmptyState
            variant="error"
            message={errorMessage(evidenceQuery.error)}
            onRetry={() => {
              void evidenceQuery.refetch();
            }}
          />
        ) : null}

        {!evidenceQuery.isLoading &&
        !evidenceQuery.isError &&
        (evidenceQuery.data?.items.length ?? 0) === 0 ? (
          <EvidenceEmptyState
            variant={hasFilters ? "filtered" : "none"}
            onClearFilters={hasFilters ? clearFilters : undefined}
          />
        ) : null}

        {!evidenceQuery.isLoading &&
        !evidenceQuery.isError &&
        (evidenceQuery.data?.items.length ?? 0) > 0 ? (
          <EvidenceList items={evidenceQuery.data?.items ?? []} />
        ) : null}
      </div>
    </section>
  );
}

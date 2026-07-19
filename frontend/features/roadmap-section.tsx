"use client";

import { ApiClientError } from "@/lib/api/error";
import type { RoadmapItem, RoadmapPriority } from "@/lib/api/types/roadmap";
import { useRoadmapQuery } from "@/lib/roadmap/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The roadmap could not be loaded. Please try again.";
}

function priorityLabel(priority: RoadmapPriority): string {
  switch (priority) {
    case "high":
      return "High priority";
    case "medium":
      return "Medium priority";
    case "low":
      return "Low priority";
  }
}

function SkillList({
  label,
  skills
}: Readonly<{ label: string; skills: string[] }>) {
  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      {skills.length === 0 ? (
        <p className="mt-1 text-sm text-secondary">None</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {skills.map((skill) => (
            <li
              key={skill}
              className="rounded-button border border-border bg-surface px-3 py-1 text-sm text-ink"
            >
              {skill}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RoadmapCard({ item }: Readonly<{ item: RoadmapItem }>) {
  return (
    <li className="rounded-card border border-border bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">{item.title}</p>
          <p className="mt-1 text-sm text-secondary">{priorityLabel(item.priority)}</p>
        </div>
      </div>

      <p className="mt-3 text-sm leading-6 text-secondary">{item.reason}</p>

      <div className="mt-4 space-y-4">
        <SkillList label="Related skills" skills={item.related_skills} />
        <SkillList label="Missing skills" skills={item.missing_skills} />
      </div>
    </li>
  );
}

export function RoadmapSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const roadmapQuery = useRoadmapQuery(enabled);

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
        aria-labelledby="roadmap-section-title"
      >
        <h2 id="roadmap-section-title" className="text-xl font-semibold text-ink">
          Roadmap
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          The roadmap is available only to candidate accounts.
        </p>
      </section>
    );
  }

  const items = roadmapQuery.data?.items ?? [];

  return (
    <section
      className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
      aria-labelledby="roadmap-section-title"
    >
      <h2 id="roadmap-section-title" className="text-xl font-semibold text-ink">
        Roadmap
      </h2>
      <p className="mt-2 text-sm text-secondary">
        Deterministic next-step recommendations based on your Skill Passport.
      </p>

      <div className="mt-6">
        {roadmapQuery.isLoading ? (
          <p className="text-sm text-secondary" role="status">
            Loading roadmap…
          </p>
        ) : null}

        {roadmapQuery.isError ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(roadmapQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void roadmapQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Try again
            </button>
          </div>
        ) : null}

        {roadmapQuery.isSuccess && items.length === 0 ? (
          <p className="text-sm text-secondary">
            No recommendations yet. Collect more skill evidence — for example by
            analyzing a GitHub repository — to unlock roadmap suggestions.
          </p>
        ) : null}

        {items.length > 0 ? (
          <ul className="space-y-3">
            {items.map((item) => (
              <RoadmapCard key={item.id} item={item} />
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}

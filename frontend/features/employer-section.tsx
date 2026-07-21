"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useQueries } from "@tanstack/react-query";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { Input, controlClassName } from "@/components/ui/input";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import { ApiClientError } from "@/lib/api/error";
import { listVacancyMatches, listVacancyRequirements } from "@/lib/api/employer";
import type {
  Vacancy,
  VacancyMatch,
  VacancyRequirement,
  VacancyRequirementType
} from "@/lib/api/types/employer";
import {
  useAddVacancyRequirement,
  useCreateEmployerCompany,
  useCreateEmployerVacancy,
  useDeleteVacancyRequirement,
  useEmployerCompanyQuery,
  useEmployerSkillsQuery,
  useEmployerVacanciesQuery,
  useEmployerVacancyQuery,
  useVacancyMatchesQuery,
  useVacancyRequirementsQuery,
  vacancyMatchesQueryKey,
  vacancyRequirementsQueryKey
} from "@/lib/employer/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The employer request failed. Please try again.";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function statusLabel(status: Vacancy["status"]): string {
  switch (status) {
    case "draft":
      return "Draft";
    case "open":
      return "Open";
    case "closed":
      return "Closed";
  }
}

function vacancyStatusTone(status: Vacancy["status"]): string {
  if (status === "open") {
    return "completed";
  }
  if (status === "closed") {
    return "failed";
  }
  return "pending";
}

function parseRequirementType(value: string): VacancyRequirementType {
  return value === "preferred" ? "preferred" : "required";
}

function VacancyRequirements({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const requirementsQuery = useVacancyRequirementsQuery(vacancyId, true);
  const skillsQuery = useEmployerSkillsQuery(true);
  const addRequirement = useAddVacancyRequirement(vacancyId);
  const deleteRequirement = useDeleteVacancyRequirement(vacancyId);
  const [skillId, setSkillId] = useState("");
  const [requirementType, setRequirementType] = useState<VacancyRequirementType>("required");

  function onAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!skillId || addRequirement.isPending) {
      return;
    }
    addRequirement.mutate(
      { skill_id: skillId, requirement_type: requirementType },
      {
        onSuccess: () => {
          setSkillId("");
          setRequirementType("required");
        }
      }
    );
  }

  function onDelete(requirement: VacancyRequirement) {
    if (deleteRequirement.isPending) {
      return;
    }
    deleteRequirement.mutate(requirement.id);
  }

  const linkedSkillIds = new Set(
    (requirementsQuery.data ?? []).map((requirement) => requirement.skill_id)
  );
  const availableSkills = (skillsQuery.data ?? []).filter(
    (skill) => !linkedSkillIds.has(skill.id)
  );
  const requiredRequirements = (requirementsQuery.data ?? []).filter(
    (requirement) => requirement.requirement_type === "required"
  );
  const preferredRequirements = (requirementsQuery.data ?? []).filter(
    (requirement) => requirement.requirement_type === "preferred"
  );

  function requirementList(
    title: string,
    requirements: VacancyRequirement[],
    tone: "danger" | "accent"
  ) {
    return (
      <section aria-label={title}>
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-sm font-medium text-ink">{title}</h4>
          <Badge variant={tone}>{requirements.length}</Badge>
        </div>
        {requirements.length > 0 ? (
          <ul className="mt-3 flex flex-wrap gap-2">
            {requirements.map((requirement) => (
              <li key={requirement.id} className="inline-flex max-w-full items-center gap-2 rounded-full border border-border bg-background px-3 py-1.5 text-sm text-ink">
                <span className="truncate">{requirement.skill_name}</span>
                <span className="text-xs text-secondary">{requirement.skill_category}</span>
                <Button type="button" variant="ghost" size="sm" onClick={() => onDelete(requirement)} loading={deleteRequirement.isPending} className="-mr-2 min-h-7 px-2 text-danger" aria-label={`Remove ${requirement.skill_name}`}>Remove</Button>
              </li>
            ))}
          </ul>
        ) : <p className="mt-2 text-sm text-secondary">No {title.toLowerCase()} configured.</p>}
      </section>
    );
  }

  return (
    <section id={`vacancy-requirements-${vacancyId}`} aria-labelledby={`vacancy-requirements-title-${vacancyId}`} className="space-y-5 border-t border-border pt-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Vacancy setup</p>
          <h3 id={`vacancy-requirements-title-${vacancyId}`} className="mt-1 text-lg font-semibold tracking-tight text-ink">Requirements</h3>
          <p className="mt-1 text-sm leading-6 text-secondary">Required and preferred skills guide the existing candidate match results.</p>
        </div>
        <Badge variant="neutral">{(requirementsQuery.data ?? []).length} configured</Badge>
      </div>

      {requirementsQuery.isLoading || skillsQuery.isLoading ? (
        <div role="status" aria-label="Loading vacancy requirements">
          <SkeletonListRow />
        </div>
      ) : null}

      {requirementsQuery.isError ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(requirementsQuery.error)}
        </p>
      ) : null}

      {requirementsQuery.isSuccess && requirementsQuery.data.length === 0 ? (
        <EmptyState title="Requirements are not configured" description="Add the skills needed for this vacancy before relying on candidate match results." className="py-6 text-left" />
      ) : null}

      {requirementsQuery.data && requirementsQuery.data.length > 0 ? (
        <div className="grid gap-5 sm:grid-cols-2">
          {requirementList("Required skills", requiredRequirements, "danger")}
          {requirementList("Preferred skills", preferredRequirements, "accent")}
        </div>
      ) : null}

      <form className="space-y-3 rounded-xl border border-border bg-surface-subtle/60 p-4" onSubmit={onAdd}>
        <div>
          <h4 className="text-sm font-medium text-ink">Add a requirement</h4>
          <p className="mt-1 text-sm text-secondary">Use the existing skills catalog for this vacancy.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <label
              htmlFor={`vacancy-skill-${vacancyId}`}
              className="block text-sm font-medium text-ink"
            >
              Skill
            </label>
            <select
              id={`vacancy-skill-${vacancyId}`}
              value={skillId}
              onChange={(event) => setSkillId(event.target.value)}
              disabled={addRequirement.isPending || availableSkills.length === 0}
              required
              className={cn(controlClassName, "min-h-control px-3")}
            >
              <option value="">Select a skill</option>
              {availableSkills.map((skill) => (
                <option key={skill.id} value={skill.id}>
                  {skill.name} ({skill.category})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label
              htmlFor={`vacancy-requirement-type-${vacancyId}`}
              className="block text-sm font-medium text-ink"
            >
              Type
            </label>
            <select
              id={`vacancy-requirement-type-${vacancyId}`}
              value={requirementType}
              onChange={(event) => setRequirementType(parseRequirementType(event.target.value))}
              disabled={addRequirement.isPending}
              className={cn(controlClassName, "min-h-control px-3")}
            >
              <option value="required">Required</option>
              <option value="preferred">Preferred</option>
            </select>
          </div>
        </div>

        {skillsQuery.isSuccess && skillsQuery.data.length === 0 ? (
          <p className="text-sm text-secondary">
            No skills are available in the ontology yet. Skills appear after candidate evidence
            extraction populates the catalog.
          </p>
        ) : null}

        {addRequirement.isError ? (
          <p className="text-sm text-danger" role="alert">
            {errorMessage(addRequirement.error)}
          </p>
        ) : null}

        {deleteRequirement.isError ? (
          <p className="text-sm text-danger" role="alert">
            {errorMessage(deleteRequirement.error)}
          </p>
        ) : null}

        <Button
          type="submit"
          variant="primary"
          disabled={!skillId || availableSkills.length === 0}
          loading={addRequirement.isPending}
        >
          Add requirement
        </Button>
      </form>
    </section>
  );
}

function VacancyDetail({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const detailQuery = useEmployerVacancyQuery(vacancyId, true);

  if (detailQuery.isLoading) {
    return (
      <div className="mt-5 space-y-3 border-t border-border pt-5" role="status" aria-label="Loading vacancy workspace"><SkeletonListRow /><SkeletonCard className="min-h-48" /></div>
    );
  }

  if (detailQuery.isError) {
    return (
      <p className="mt-3 text-sm text-danger" role="alert">
        {errorMessage(detailQuery.error)}
      </p>
    );
  }

  const vacancy = detailQuery.data;
  if (!vacancy) {
    return null;
  }

  return (
    <section id={`vacancy-details-${vacancyId}`} aria-labelledby={`vacancy-context-title-${vacancyId}`} className="mt-5 space-y-7 border-t border-border pt-5">
      <header className="flex flex-col gap-4 rounded-xl border border-border bg-surface-subtle/60 p-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Vacancy workspace</p><h3 id={`vacancy-context-title-${vacancyId}`} className="mt-1 break-words text-xl font-semibold tracking-tight text-ink">{vacancy.title}</h3><p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">{vacancy.description?.trim() ? vacancy.description : "No description provided."}</p></div>
        <div className="flex shrink-0 flex-wrap items-center gap-2"><StatusBadge status={vacancyStatusTone(vacancy.status)} label={statusLabel(vacancy.status)} /><span className="text-sm text-secondary">Created {formatDate(vacancy.created_at)}</span></div>
      </header>
      <VacancyRequirements vacancyId={vacancyId} />
      <VacancyMatches vacancyId={vacancyId} />
    </section>
  );
}

function MatchCard({
  match,
  vacancyId
}: Readonly<{ match: VacancyMatch; vacancyId: string }>) {
  const href = `/employer/matches/${match.candidate_id}?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const requiredTotal = match.required.matched.length + match.required.missing.length;
  const preferredTotal = match.preferred.matched.length + match.preferred.missing.length;

  return (
    <li className="rounded-xl border border-border bg-background p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0"><p className="break-words text-base font-semibold text-ink">{match.candidate_name}</p><p className="mt-1 text-sm text-secondary">Candidate match for this vacancy</p></div>
        <div className="shrink-0 text-left sm:text-right"><p className="text-xl font-semibold tabular-nums text-ink">{match.score}%</p><p className="text-xs font-medium uppercase tracking-wide text-secondary">Vacancy match</p></div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-subtle" role="progressbar" aria-label={`${match.candidate_name} vacancy match`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={match.score}><div className="h-full rounded-full bg-primary transition-[width] duration-200" style={{ width: `${match.score}%` }} /></div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-lg bg-surface-subtle/70 p-3"><dt className="text-secondary">Required skills</dt><dd className="mt-1 font-medium text-ink">{match.required.matched.length} matched{requiredTotal > 0 ? ` of ${requiredTotal}` : ""}</dd>{match.required.missing.length > 0 ? <p className="mt-1 text-xs leading-5 text-secondary">{match.required.missing.length} missing</p> : null}</div>
        <div className="rounded-lg bg-surface-subtle/70 p-3"><dt className="text-secondary">Preferred skills</dt><dd className="mt-1 font-medium text-ink">{match.preferred.matched.length} matched{preferredTotal > 0 ? ` of ${preferredTotal}` : ""}</dd>{match.preferred.missing.length > 0 ? <p className="mt-1 text-xs leading-5 text-secondary">{match.preferred.missing.length} missing</p> : null}</div>
      </dl>
      <div className="mt-4 border-t border-border pt-4"><Link href={href} className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2" aria-label={`Review candidate ${match.candidate_name}`}>Review candidate</Link></div>
    </li>
  );
}

function VacancyMatches({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const matchesQuery = useVacancyMatchesQuery(vacancyId, true);
  const matches = matchesQuery.data?.matches ?? [];

  return (
    <section id={`vacancy-matches-${vacancyId}`} aria-labelledby={`vacancy-matches-title-${vacancyId}`} className="space-y-5 border-t border-border pt-5">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Candidate review</p><h3 id={`vacancy-matches-title-${vacancyId}`} className="mt-1 text-lg font-semibold tracking-tight text-ink">Candidate matches</h3><p className="mt-1 text-sm leading-6 text-secondary">Results are shown in the existing match order for this vacancy.</p></div>{matchesQuery.data ? <Badge variant="neutral">{matches.length} {matches.length === 1 ? "candidate" : "candidates"}</Badge> : null}</div>

      {matchesQuery.isLoading ? (
        <div role="status" aria-label="Loading candidate matches">
          <SkeletonListRow />
        </div>
      ) : null}

      {matchesQuery.isError ? (
        <EmptyState
          role="alert"
          title="Could not load matches"
          description={errorMessage(matchesQuery.error)}
          primaryAction={
            <Button type="button" variant="secondary" onClick={() => void matchesQuery.refetch()}>
              Try again
            </Button>
          }
          className="py-4"
        />
      ) : null}

      {matchesQuery.isSuccess && matches.length === 0 ? (
        <EmptyState title="No candidate matches yet" description="No candidates currently match this vacancy." className="py-6" />
      ) : null}

      {matches.length > 0 ? (
        <ul className="space-y-3">
          {matches.map((match) => (
            <MatchCard key={match.candidate_id} match={match} vacancyId={vacancyId} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function VacancyCard({
  vacancy,
  requirementsCount,
  matches,
  selected,
  onSelect
}: Readonly<{
  vacancy: Vacancy;
  requirementsCount: number;
  matches: VacancyMatch[];
  selected: boolean;
  onSelect: () => void;
}>) {
  const topMatch = matches.reduce((highest, match) => Math.max(highest, match.score), 0);

  return (
    <Card className={cn("overflow-hidden bg-background", selected && "border-primary/40 ring-1 ring-primary/15")}>
        <CardContent className="p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 space-y-2">
              <p className="break-words text-lg font-semibold tracking-tight text-ink">{vacancy.title}</p>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge
                  status={vacancyStatusTone(vacancy.status)}
                  label={statusLabel(vacancy.status)}
                />
                <span className="text-sm text-secondary">Created {formatDate(vacancy.created_at)}</span>
              </div>
              {vacancy.description ? (
                <p className="line-clamp-2 text-sm leading-6 text-secondary">{vacancy.description}</p>
              ) : null}
            </div>
          </div>
          <dl className="mt-5 grid grid-cols-3 divide-x divide-border rounded-xl border border-border bg-surface-subtle/70 text-center">
            <div className="p-3"><dt className="text-xs text-secondary">Requirements</dt><dd className="mt-1 text-lg font-semibold tabular-nums text-ink">{requirementsCount}</dd></div>
            <div className="p-3"><dt className="text-xs text-secondary">Matches</dt><dd className="mt-1 text-lg font-semibold tabular-nums text-ink">{matches.length}</dd></div>
            <div className="p-3"><dt className="text-xs text-secondary">Top match</dt><dd className="mt-1 text-lg font-semibold tabular-nums text-ink">{topMatch}%</dd></div>
          </dl>
          <div className="mt-5 flex flex-wrap gap-2">
            <Button type="button" variant={selected ? "secondary" : "primary"} size="sm" onClick={onSelect} aria-pressed={selected} aria-controls={`selected-vacancy-workspace-${vacancy.id}`}>{selected ? "Selected vacancy" : "Manage vacancy"}</Button>
          </div>
        </CardContent>
    </Card>
  );
}

function SelectedVacancyWorkspace({
  vacancy,
  onClose
}: Readonly<{
  vacancy: Vacancy;
  onClose: () => void;
}>) {
  return (
    <section id={`selected-vacancy-workspace-${vacancy.id}`} aria-labelledby={`selected-vacancy-title-${vacancy.id}`} className="mt-8 rounded-card border border-primary/20 bg-surface p-5 shadow-card sm:p-6">
      <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Selected vacancy workspace</p><h3 id={`selected-vacancy-title-${vacancy.id}`} className="mt-1 break-words text-2xl font-semibold tracking-tight text-ink">{vacancy.title}</h3><p className="mt-2 text-sm leading-6 text-secondary">Configure requirements and review the candidate matches returned for this vacancy.</p></div>
        <Button type="button" variant="secondary" size="sm" onClick={onClose}>Close workspace</Button>
      </div>
      <VacancyDetail vacancyId={vacancy.id} />
    </section>
  );
}

function TopMatchesByVacancy({
  vacancies,
  matchesByVacancy,
  onViewMatches
}: Readonly<{
  vacancies: Vacancy[];
  matchesByVacancy: VacancyMatch[][];
  onViewMatches: (vacancyId: string) => void;
}>) {
  return (
    <section id="top-matches-by-vacancy" aria-labelledby="top-matches-by-vacancy-title">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Candidate review</p>
          <h2 id="top-matches-by-vacancy-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">Candidate matches</h2>
          <p className="mt-2 text-sm leading-6 text-secondary">Review the strongest available candidate for each vacancy in its existing order.</p>
        </div>
        <Badge variant="neutral">{vacancies.length} vacancies</Badge>
      </div>
      <ul className="mt-5 grid gap-4 lg:grid-cols-2">
        {vacancies.map((vacancy, index) => {
          const matches = matchesByVacancy[index] ?? [];
          const bestMatch = matches[0];

          return (
            <li key={vacancy.id}>
              <Card className="h-full bg-background">
                <CardContent className="p-5">
                  <p className="font-medium text-ink">{vacancy.title}</p>
                  {bestMatch ? (
                    <div className="mt-4 flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-secondary">Best available match</p>
                        <p className="mt-1 text-sm font-medium text-ink">{bestMatch.candidate_name}</p>
                      </div>
                      <Badge variant={bestMatch.score >= 75 ? "success" : bestMatch.score >= 50 ? "primary" : "neutral"}>{bestMatch.score}% match</Badge>
                    </div>
                  ) : <p className="mt-4 text-sm text-secondary">No candidate matches yet.</p>}
                  <div className="mt-5 flex items-center justify-between gap-3 border-t border-border pt-4">
                    <span className="text-sm text-secondary">{matches.length} {matches.length === 1 ? "candidate" : "candidates"}</span>
                    <Button type="button" variant="secondary" size="sm" onClick={() => onViewMatches(vacancy.id)} aria-label={`Manage ${vacancy.title}`}>Manage vacancy</Button>
                  </div>
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function EmployerDashboard({ enabled }: Readonly<{ enabled: boolean }>) {
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null);
  const vacanciesQuery = useEmployerVacanciesQuery(enabled);
  const vacancies = [...(vacanciesQuery.data ?? [])].sort(
    (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
  );
  const requirementQueries = useQueries({
    queries: vacancies.map((vacancy) => ({
      queryKey: vacancyRequirementsQueryKey(vacancy.id),
      queryFn: () => listVacancyRequirements(vacancy.id),
      enabled,
      staleTime: 30_000
    }))
  });
  const matchQueries = useQueries({
    queries: vacancies.map((vacancy) => ({
      queryKey: vacancyMatchesQueryKey(vacancy.id),
      queryFn: () => listVacancyMatches(vacancy.id),
      enabled,
      staleTime: 30_000
    }))
  });
  const activeVacancies = vacancies.filter((vacancy) => vacancy.status === "open").length;

  function openMatches(vacancyId: string) {
    setSelectedVacancyId(vacancyId);
    window.requestAnimationFrame(() => {
      document.getElementById(`selected-vacancy-workspace-${vacancyId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (!enabled) return null;
  if (vacanciesQuery.isLoading) return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" role="status" aria-label="Loading employer dashboard"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>;
  if (vacanciesQuery.isError) return <EmptyState role="alert" title="Employer dashboard unavailable" description={errorMessage(vacanciesQuery.error)} primaryAction={<Button variant="secondary" onClick={() => void vacanciesQuery.refetch()}>Try again</Button>} />;

  const attentionItems = vacancies.flatMap((vacancy, index) => {
    const requirements = requirementQueries[index]?.data;
    const matches = matchQueries[index]?.data?.matches;
    const items: Array<{ id: string; title: string; description: string; action: string }> = [];

    if (requirements?.length === 0) {
      items.push({ id: `${vacancy.id}-requirements`, title: `${vacancy.title} needs requirements`, description: "Add the skills used to evaluate candidate matches.", action: "Add requirements" });
    }
    if (matches?.length === 0) {
      items.push({ id: `${vacancy.id}-matches`, title: `${vacancy.title} has no matches yet`, description: "Matches appear when candidate evidence is available.", action: "Review vacancy" });
    }

    return items.map((item) => ({ ...item, vacancyId: vacancy.id }));
  });
  const selectedVacancy = vacancies.find((vacancy) => vacancy.id === selectedVacancyId) ?? null;

  return (
    <section id="employer-overview" className="space-y-12">
      <section aria-labelledby="employer-dashboard-title" className="rounded-card border border-primary/15 bg-primary/[0.04] p-5 shadow-card sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Today’s hiring workspace</p>
            <h2 id="employer-dashboard-title" className="mt-2 text-2xl font-semibold tracking-tight text-ink">What needs your attention?</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">Review current vacancy setup and available candidate matches using the existing hiring data.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href="#create-vacancy" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Create vacancy</a>
            <a href="#top-matches-by-vacancy" className="inline-flex min-h-control items-center rounded-button border border-border bg-background px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Review matches</a>
          </div>
        </div>
        <div className="mt-6 border-t border-primary/10 pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-base font-semibold text-ink">Needs attention</h3><Badge variant={attentionItems.length > 0 ? "primary" : "success"}>{attentionItems.length > 0 ? `${attentionItems.length} items` : "Up to date"}</Badge></div>
          {attentionItems.length > 0 ? (
            <ul className="mt-4 grid gap-3 lg:grid-cols-2">
              {attentionItems.map((item) => (
                <li key={item.id} className="flex flex-col justify-between gap-4 rounded-xl border border-border bg-background p-4 sm:flex-row sm:items-center">
                  <div><p className="text-sm font-medium text-ink">{item.title}</p><p className="mt-1 text-sm leading-5 text-secondary">{item.description}</p></div>
                  <Button type="button" variant="secondary" size="sm" onClick={() => openMatches(item.vacancyId)}>{item.action}</Button>
                </li>
              ))}
            </ul>
          ) : <p className="mt-3 text-sm leading-6 text-secondary">No current vacancy setup needs attention.</p>}
        </div>
      </section>

      <div id="employer-vacancies">
        {vacancies.length === 0 ? (
          <EmptyState icon={<Icon name="employer" className="h-8 w-8" />} title="Create your first vacancy" description="Add an opening and its requirements to start discovering candidates through verified skills and evidence." primaryAction={<a href="#create-vacancy" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Create your first vacancy</a>} className="py-12" />
        ) : (
          <>
            <section aria-labelledby="vacancies-title">
              <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Hiring pipeline</p><h2 id="vacancies-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">Active vacancies</h2><p className="mt-2 text-sm leading-6 text-secondary">Review vacancy status, requirements, and current candidate matches.</p></div><Badge variant="primary">{activeVacancies} open</Badge></div>
              <ul className="mt-5 grid items-start gap-4 xl:grid-cols-2">{vacancies.map((vacancy, index) => <li id={`vacancy-card-${vacancy.id}`} key={vacancy.id}><VacancyCard vacancy={vacancy} requirementsCount={requirementQueries[index]?.data?.length ?? 0} matches={matchQueries[index]?.data?.matches ?? []} selected={selectedVacancyId === vacancy.id} onSelect={() => openMatches(vacancy.id)} /></li>)}</ul>
              {selectedVacancy ? <SelectedVacancyWorkspace vacancy={selectedVacancy} onClose={() => setSelectedVacancyId(null)} /> : null}
            </section>
            <TopMatchesByVacancy vacancies={vacancies} matchesByVacancy={matchQueries.map((query) => query.data?.matches ?? [])} onViewMatches={openMatches} />
          </>
        )}
      </div>
    </section>
  );
}

function CompanyPanel({ enabled }: Readonly<{ enabled: boolean }>) {
  const companyQuery = useEmployerCompanyQuery(enabled);
  const createCompany = useCreateEmployerCompany();
  const [companyName, setCompanyName] = useState("");
  const [website, setWebsite] = useState("");
  const [description, setDescription] = useState("");

  const companyMissing =
    companyQuery.isError &&
    companyQuery.error instanceof ApiClientError &&
    companyQuery.error.status === 404;

  function onCreateCompany(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = companyName.trim();
    if (!trimmedName || createCompany.isPending) {
      return;
    }
    createCompany.mutate({
      company_name: trimmedName,
      website: website.trim() || null,
      description: description.trim() || null
    });
  }

  if (companyQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading company">
        <SkeletonCard />
      </div>
    );
  }

  if (companyQuery.isError && !companyMissing) {
    return (
      <EmptyState
        role="alert"
        title="Could not load company"
        description={errorMessage(companyQuery.error)}
        primaryAction={
          <Button type="button" variant="secondary" onClick={() => void companyQuery.refetch()}>
            Try again
          </Button>
        }
      />
    );
  }

  if (companyQuery.data) {
    const company = companyQuery.data;
    return (
      <Card className="bg-background">
        <CardContent className="space-y-2 p-4">
          <p className="text-sm font-medium text-ink">{company.company_name}</p>
          {company.website ? (
            <p className="break-all text-sm text-secondary">
              <a
                href={company.website}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-primary underline-offset-2 hover:underline"
              >
                {company.website}
              </a>
            </p>
          ) : null}
          <p className="text-sm leading-6 text-secondary">
            {company.description?.trim() ? company.description : "No company description."}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-background">
      <CardContent className="space-y-4 p-4">
        <div id="employer-company">
          <p className="text-sm font-medium text-ink">Create your company</p>
          <p className="mt-2 text-sm text-secondary">
            Register company details before posting vacancies.
          </p>
        </div>
        <form className="space-y-4" onSubmit={onCreateCompany}>
          <div className="space-y-2">
            <label htmlFor="employer-company-name" className="block text-sm font-medium text-ink">
              Company name
            </label>
            <Input
              id="employer-company-name"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              disabled={createCompany.isPending}
              maxLength={160}
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="employer-company-website" className="block text-sm font-medium text-ink">
              Website
            </label>
            <Input
              id="employer-company-website"
              type="url"
              value={website}
              onChange={(event) => setWebsite(event.target.value)}
              disabled={createCompany.isPending}
              placeholder="https://example.com"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="employer-company-description"
              className="block text-sm font-medium text-ink"
            >
              Description
            </label>
            <textarea
              id="employer-company-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={createCompany.isPending}
              rows={3}
              maxLength={5000}
              className={cn(controlClassName, "px-3 py-2")}
            />
          </div>
          {createCompany.isError ? (
            <p className="text-sm text-danger" role="alert">
              {errorMessage(createCompany.error)}
            </p>
          ) : null}
          <Button
            type="submit"
            variant="primary"
            disabled={!companyName.trim()}
            loading={createCompany.isPending}
          >
            Create company
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function VacanciesPanel({ enabled }: Readonly<{ enabled: boolean }>) {
  const createVacancy = useCreateEmployerVacancy();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  function onCreateVacancy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle || createVacancy.isPending) {
      return;
    }
    createVacancy.mutate(
      {
        title: trimmedTitle,
        description: description.trim() || null,
        status: "open"
      },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
        }
      }
    );
  }

  if (!enabled) {
    return (
      <p className="text-sm text-secondary">Create a company to start posting vacancies.</p>
    );
  }

  return (
    <div className="space-y-4">
      <Card id="create-vacancy" className="bg-background">
        <CardContent className="space-y-4 p-4">
          <p className="text-sm font-medium text-ink">Create vacancy</p>
          <form className="space-y-4" onSubmit={onCreateVacancy}>
            <div className="space-y-2">
              <label htmlFor="employer-vacancy-title" className="block text-sm font-medium text-ink">
                Title
              </label>
              <Input
                id="employer-vacancy-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                disabled={createVacancy.isPending}
                maxLength={200}
                required
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="employer-vacancy-description"
                className="block text-sm font-medium text-ink"
              >
                Short description
              </label>
              <textarea
                id="employer-vacancy-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                disabled={createVacancy.isPending}
                rows={3}
                maxLength={5000}
                className={cn(controlClassName, "px-3 py-2")}
              />
            </div>
            {createVacancy.isError ? (
              <p className="text-sm text-danger" role="alert">
                {errorMessage(createVacancy.error)}
              </p>
            ) : null}
            <Button
              type="submit"
              variant="primary"
              disabled={!title.trim()}
              loading={createVacancy.isPending}
            >
              Create vacancy
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export function EmployerSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const companyQuery = useEmployerCompanyQuery(enabled);
  const hasCompany = Boolean(companyQuery.data);
  const companyMissing =
    companyQuery.isError &&
    companyQuery.error instanceof ApiClientError &&
    companyQuery.error.status === 404;

  if (!enabled) {
    return (
      <Card className="lg:col-span-2" aria-labelledby="employer-section-title">
        <CardContent className="p-6">
          <div className="flex gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/10" aria-hidden="true"><Icon name="employer" className="h-[18px] w-[18px]" /></span>
            <div><h2 id="employer-section-title" className="text-xl font-semibold text-ink">Employer</h2><p className="mt-2 text-sm leading-6 text-secondary">The employer workspace is available only to employer accounts.</p></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <section className="space-y-12 lg:col-span-2" aria-labelledby="employer-section-title">
      <h2 id="employer-section-title" className="sr-only">Employer dashboard</h2>

      {companyMissing ? (
        <section aria-labelledby="company-attention-title" className="rounded-card border border-primary/15 bg-primary/[0.04] p-5 shadow-card sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Needs attention</p>
          <div className="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h2 id="company-attention-title" className="text-2xl font-semibold tracking-tight text-ink">Set up your company profile</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">Add your company details before posting vacancies and reviewing candidate matches.</p></div><a href="#employer-company" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Set up company</a></div>
        </section>
      ) : null}

      {hasCompany ? <EmployerDashboard enabled /> : null}

      <section id="employer-company" aria-labelledby="company-overview-title">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Organization</p><h2 id="company-overview-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">Company overview</h2><p className="mt-2 text-sm leading-6 text-secondary">Keep the company information used for your existing vacancies in one place.</p></div></div>
        <div className="mt-5"><CompanyPanel enabled={enabled} /></div>
      </section>

      <section aria-labelledby="quick-actions-title">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Hiring workflow</p><h2 id="quick-actions-title" className="mt-1 text-2xl font-semibold tracking-tight text-ink">Quick actions</h2><p className="mt-2 text-sm leading-6 text-secondary">Create a new vacancy using the same existing workflow.</p></div>
        <div className="mt-5"><VacanciesPanel enabled={hasCompany} /></div>
      </section>
    </section>
  );
}

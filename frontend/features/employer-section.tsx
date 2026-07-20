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
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import { ApiClientError } from "@/lib/api/error";
import { listVacancyMatches, listVacancyRequirements } from "@/lib/api/employer";
import type {
  MatchSkillGroup,
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

function requirementTypeLabel(value: VacancyRequirementType): string {
  return value === "required" ? "Required" : "Preferred";
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

  return (
    <div className="mt-4 space-y-3 border-t border-border pt-3">
      <p className="text-sm font-medium text-ink">Requirements</p>

      {requirementsQuery.isLoading || skillsQuery.isLoading ? (
        <div role="status" aria-label="Loading requirements">
          <SkeletonListRow />
        </div>
      ) : null}

      {requirementsQuery.isError ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(requirementsQuery.error)}
        </p>
      ) : null}

      {requirementsQuery.isSuccess && requirementsQuery.data.length === 0 ? (
        <p className="text-sm text-secondary">No skill requirements yet.</p>
      ) : null}

      {requirementsQuery.data && requirementsQuery.data.length > 0 ? (
        <ul className="space-y-2">
          {requirementsQuery.data.map((requirement) => (
            <li
              key={requirement.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-button border border-border bg-surface px-3 py-2 text-sm"
            >
              <span className="min-w-0 break-words text-ink">
                {requirement.skill_name}
                <span className="ml-2 text-secondary">
                  <Badge
                    variant={requirement.requirement_type === "required" ? "danger" : "accent"}
                    className="align-middle"
                  >
                    {requirementTypeLabel(requirement.requirement_type)}
                  </Badge>{" "}
                  · {requirement.skill_category}
                </span>
              </span>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => onDelete(requirement)}
                loading={deleteRequirement.isPending}
                className="text-danger"
              >
                Remove
              </Button>
            </li>
          ))}
        </ul>
      ) : null}

      <form className="space-y-3" onSubmit={onAdd}>
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
    </div>
  );
}

function VacancyDetail({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const detailQuery = useEmployerVacancyQuery(vacancyId, true);

  if (detailQuery.isLoading) {
    return (
      <div className="mt-3" role="status" aria-label="Loading vacancy">
        <SkeletonListRow />
      </div>
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
    <div className="mt-3 space-y-2 border-t border-border pt-3 text-sm text-secondary">
      <div className="flex flex-wrap items-center gap-2">
        <span>Status:</span>
        <StatusBadge status={vacancyStatusTone(vacancy.status)} label={statusLabel(vacancy.status)} />
      </div>
      <p>
        Created: <span className="font-medium text-ink">{formatDate(vacancy.created_at)}</span>
      </p>
      <p className="leading-6">
        {vacancy.description?.trim() ? vacancy.description : "No description provided."}
      </p>
      <VacancyRequirements vacancyId={vacancyId} />
      <VacancyMatches vacancyId={vacancyId} />
    </div>
  );
}

function skillGroupText(group: MatchSkillGroup, emptyLabel: string): string {
  const matched =
    group.matched.length > 0 ? `Matched: ${group.matched.join(", ")}` : "Matched: none";
  const missing =
    group.missing.length > 0 ? `Missing: ${group.missing.join(", ")}` : emptyLabel;
  return `${matched}. ${missing}`;
}

function MatchCard({
  match,
  vacancyId
}: Readonly<{ match: VacancyMatch; vacancyId: string }>) {
  const href = `/employer/matches/${match.candidate_id}?vacancy_id=${encodeURIComponent(vacancyId)}`;

  return (
    <li>
      <Link
        href={href}
        className="block rounded-card border border-border bg-surface p-3 transition-colors hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        aria-label={`Open profile for ${match.candidate_name}, match score ${match.score}`}
      >
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="min-w-0 break-words text-sm font-medium text-ink">{match.candidate_name}</p>
          <p className="text-sm font-medium tabular-nums text-ink">Score {match.score}</p>
        </div>
        <p className="mt-2 text-sm text-secondary">
          Required — {skillGroupText(match.required, "Missing: none")}
        </p>
        <p className="mt-1 text-sm text-secondary">
          Preferred — {skillGroupText(match.preferred, "Missing: none")}
        </p>
        <p className="mt-3 text-sm font-medium text-primary">View profile →</p>
      </Link>
    </li>
  );
}

function VacancyMatches({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const matchesQuery = useVacancyMatchesQuery(vacancyId, true);
  const matches = matchesQuery.data?.matches ?? [];

  return (
    <div className="mt-4 space-y-3 border-t border-border pt-3">
      <p className="text-sm font-medium text-ink">Matches</p>

      {matchesQuery.isLoading ? (
        <div role="status" aria-label="Loading matches">
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
        <p className="text-sm text-secondary">No candidates available to match yet.</p>
      ) : null}

      {matches.length > 0 ? (
        <ul className="space-y-2">
          {matches.map((match) => (
            <MatchCard key={match.candidate_id} match={match} vacancyId={vacancyId} />
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function VacancyCard({
  vacancy,
  requirementsCount,
  matches
}: Readonly<{ vacancy: Vacancy; requirementsCount: number; matches: VacancyMatch[] }>) {
  const [open, setOpen] = useState(false);
  const topMatch = matches.reduce((highest, match) => Math.max(highest, match.score), 0);

  return (
    <li>
      <Card className="overflow-hidden bg-background transition duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
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
                <p className="line-clamp-2 text-sm text-secondary">{vacancy.description}</p>
              ) : null}
            </div>
          </div>
          <div className="mt-5 grid grid-cols-3 divide-x divide-border rounded-xl border border-border bg-surface/70 text-center">
            <div className="p-3"><p className="text-lg font-semibold tabular-nums text-ink">{requirementsCount}</p><p className="mt-1 text-xs text-secondary">Requirements</p></div>
            <div className="p-3"><p className="text-lg font-semibold tabular-nums text-ink">{matches.length}</p><p className="mt-1 text-xs text-secondary">Matched</p></div>
            <div className="p-3"><p className="text-lg font-semibold tabular-nums text-ink">{topMatch}%</p><p className="mt-1 text-xs text-secondary">Top match</p></div>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-controls={`vacancy-details-${vacancy.id}`}>{open ? "Close" : "Open"}</Button>
            <Button type="button" variant="secondary" size="sm" onClick={() => setOpen(true)} aria-label={`View matches for ${vacancy.title}`}>View Matches</Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(true)} aria-label={`Edit requirements for ${vacancy.title}`}>Edit requirements</Button>
          </div>
          {open ? <div id={`vacancy-details-${vacancy.id}`}><VacancyDetail vacancyId={vacancy.id} /></div> : null}
        </CardContent>
      </Card>
    </li>
  );
}

function EmployerDashboard({ enabled }: Readonly<{ enabled: boolean }>) {
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
  const allMatches = vacancies.flatMap((vacancy, index) =>
    (matchQueries[index]?.data?.matches ?? []).map((match) => ({ vacancy, match }))
  );
  const candidateCount = new Set(allMatches.map(({ match }) => match.candidate_id)).size;
  const averageMatch = allMatches.length > 0
    ? Math.round(allMatches.reduce((total, { match }) => total + match.score, 0) / allMatches.length)
    : null;
  const activeVacancies = vacancies.filter((vacancy) => vacancy.status === "open").length;

  if (!enabled) return null;
  if (vacanciesQuery.isLoading) return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" role="status" aria-label="Loading employer dashboard"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>;
  if (vacanciesQuery.isError) return <EmptyState role="alert" title="Employer dashboard unavailable" description={errorMessage(vacanciesQuery.error)} primaryAction={<Button variant="secondary" onClick={() => void vacanciesQuery.refetch()}>Try again</Button>} />;

  const metrics = [
    ["Active vacancies", activeVacancies, "Open roles ready for matching"],
    ["Candidates matched", candidateCount, "Unique candidates across vacancies"],
    ["Average match", averageMatch === null ? "—" : `${averageMatch}%`, averageMatch === null ? "Matches appear after requirements are added" : "Across available candidate matches"],
    ["Recent activity", vacancies[0] ? formatDate(vacancies[0].created_at) : "No activity", vacancies[0] ? `Latest vacancy: ${vacancies[0].title}` : "Create a vacancy to begin"]
  ];

  return <section aria-labelledby="employer-dashboard-title" className="space-y-8">
    <div className="rounded-card border border-primary/15 bg-gradient-to-br from-primary/10 via-background to-cyan-50 p-6 shadow-card">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Recruiting overview</p><h2 id="employer-dashboard-title" className="mt-2 text-2xl font-semibold tracking-tight text-ink">Keep your hiring pipeline moving.</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">See active roles, evidence-based candidate matches, and the next action for every opening.</p></div>
        <div className="flex flex-wrap gap-2"><a href="#create-vacancy" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">+ Create Vacancy</a><a href="#recent-matches" className="inline-flex min-h-control items-center rounded-button border border-border bg-background px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Browse Candidates</a><a href="#recent-matches" className="inline-flex min-h-control items-center rounded-button border border-border bg-background px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">View Matches</a></div>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, detail]) => <Card key={label} className="bg-background/90"><CardContent className="p-4"><p className="text-sm text-secondary">{label}</p><p className="mt-2 text-xl font-semibold tracking-tight text-ink">{value}</p><p className="mt-1 text-xs leading-5 text-muted">{detail}</p></CardContent></Card>)}</div>
    </div>

    {vacancies.length === 0 ? <EmptyState icon={<Icon name="employer" className="h-8 w-8" />} title="Create your first vacancy" description="Add an opening and its requirements to start discovering candidates through verified skills and evidence." primaryAction={<a href="#create-vacancy" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Create your first vacancy</a>} className="py-12" /> : <><section aria-labelledby="vacancies-title"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 id="vacancies-title" className="text-xl font-semibold tracking-tight text-ink">Your vacancies</h2><p className="mt-1 text-sm text-secondary">Prioritize roles with requirements and candidate matches.</p></div><Badge variant="primary">{vacancies.length} total</Badge></div><ul className="mt-4 grid gap-4 xl:grid-cols-2">{vacancies.map((vacancy, index) => <VacancyCard key={vacancy.id} vacancy={vacancy} requirementsCount={requirementQueries[index]?.data?.length ?? 0} matches={matchQueries[index]?.data?.matches ?? []} />)}</ul></section>
      <section id="recent-matches" aria-labelledby="recent-matches-title" className="rounded-card border border-border bg-surface/80 p-5 shadow-card"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 id="recent-matches-title" className="text-xl font-semibold tracking-tight text-ink">Recent candidate matches</h2><p className="mt-1 text-sm text-secondary">Top available matches for your most recently created vacancies.</p></div><Badge variant="neutral">{allMatches.length} available</Badge></div>{allMatches.length === 0 ? <p className="mt-5 text-sm text-secondary">Add skill requirements to a vacancy to generate candidate matches.</p> : <ul className="mt-5 grid gap-3 lg:grid-cols-2">{allMatches.slice(0, 4).map(({ vacancy, match }) => <li key={`${vacancy.id}-${match.candidate_id}`}><Link href={`/employer/matches/${match.candidate_id}?vacancy_id=${encodeURIComponent(vacancy.id)}`} className="block rounded-xl border border-border bg-background p-4 transition hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2" aria-label={`Open ${match.candidate_name} for ${vacancy.title}`}><div className="flex items-start justify-between gap-3"><div><p className="font-medium text-ink">{match.candidate_name}</p><p className="mt-1 text-sm text-secondary">{vacancy.title}</p></div><Badge variant={match.score >= 75 ? "success" : match.score >= 50 ? "primary" : "neutral"}>{match.score}% match</Badge></div><p className="mt-3 text-sm font-medium text-primary">View match details →</p></Link></li>)}</ul>}</section></>}
  </section>;
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
        <div>
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

  if (!enabled) {
    return (
      <Card className="lg:col-span-2" aria-labelledby="employer-section-title">
        <CardContent className="p-6">
          <SectionHeader
            title="Employer"
            icon="employer"
            titleId="employer-section-title"
            description="The employer workspace is available only to employer accounts."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="lg:col-span-2" aria-labelledby="employer-section-title">
      <CardContent className="space-y-8 p-6">
        <SectionHeader
          title="Employer"
          icon="employer"
          titleId="employer-section-title"
          description="Manage your company profile and job openings."
        />

        <EmployerDashboard enabled={hasCompany} />

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-secondary">
            Company
          </h3>
          <div className="mt-3">
            <CompanyPanel enabled={enabled} />
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-secondary">Jobs</h3>
          <div className="mt-3">
            <VacanciesPanel enabled={hasCompany} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useState, type FormEvent } from "react";

import { ApiClientError } from "@/lib/api/error";
import type {
  Vacancy,
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
  useVacancyRequirementsQuery
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
        <p className="text-sm text-secondary" role="status">
          Loading requirements…
        </p>
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
              <span className="text-ink">
                {requirement.skill_name}
                <span className="ml-2 text-secondary">
                  {requirementTypeLabel(requirement.requirement_type)} ·{" "}
                  {requirement.skill_category}
                </span>
              </span>
              <button
                type="button"
                onClick={() => onDelete(requirement)}
                disabled={deleteRequirement.isPending}
                className="min-h-control rounded-button border border-border bg-background px-3 text-sm font-medium text-danger disabled:opacity-60"
              >
                Remove
              </button>
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
              className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
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
              className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
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

        <button
          type="submit"
          disabled={!skillId || addRequirement.isPending || availableSkills.length === 0}
          className="min-h-control rounded-button bg-primary px-4 text-sm font-medium text-white disabled:opacity-60"
        >
          {addRequirement.isPending ? "Adding…" : "Add requirement"}
        </button>
      </form>
    </div>
  );
}

function VacancyDetail({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const detailQuery = useEmployerVacancyQuery(vacancyId, true);

  if (detailQuery.isLoading) {
    return (
      <p className="mt-3 text-sm text-secondary" role="status">
        Loading vacancy…
      </p>
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
      <p>
        Status: <span className="font-medium text-ink">{statusLabel(vacancy.status)}</span>
      </p>
      <p>
        Created: <span className="font-medium text-ink">{formatDate(vacancy.created_at)}</span>
      </p>
      <p className="leading-6">
        {vacancy.description?.trim() ? vacancy.description : "No description provided."}
      </p>
      <VacancyRequirements vacancyId={vacancyId} />
    </div>
  );
}

function VacancyCard({ vacancy }: Readonly<{ vacancy: Vacancy }>) {
  const [open, setOpen] = useState(false);

  return (
    <li className="rounded-card border border-border bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">{vacancy.title}</p>
          <p className="mt-1 text-sm text-secondary">
            {statusLabel(vacancy.status)} · {formatDate(vacancy.created_at)}
          </p>
          {vacancy.description ? (
            <p className="mt-2 line-clamp-2 text-sm text-secondary">{vacancy.description}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          aria-expanded={open}
        >
          {open ? "Hide" : "Open"}
        </button>
      </div>
      {open ? <VacancyDetail vacancyId={vacancy.id} /> : null}
    </li>
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
      <p className="text-sm text-secondary" role="status">
        Loading company…
      </p>
    );
  }

  if (companyQuery.isError && !companyMissing) {
    return (
      <div>
        <p className="text-sm text-danger" role="alert">
          {errorMessage(companyQuery.error)}
        </p>
        <button
          type="button"
          onClick={() => void companyQuery.refetch()}
          className="mt-3 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Try again
        </button>
      </div>
    );
  }

  if (companyQuery.data) {
    const company = companyQuery.data;
    return (
      <div className="rounded-card border border-border bg-background p-4">
        <p className="text-sm font-medium text-ink">{company.company_name}</p>
        {company.website ? (
          <p className="mt-2 break-all text-sm text-secondary">
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
        <p className="mt-2 text-sm leading-6 text-secondary">
          {company.description?.trim() ? company.description : "No company description."}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-card border border-border bg-background p-4">
      <p className="text-sm font-medium text-ink">Create your company</p>
      <p className="mt-2 text-sm text-secondary">
        Register company details before posting vacancies.
      </p>
      <form className="mt-4 space-y-4" onSubmit={onCreateCompany}>
        <div className="space-y-2">
          <label htmlFor="employer-company-name" className="block text-sm font-medium text-ink">
            Company name
          </label>
          <input
            id="employer-company-name"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            disabled={createCompany.isPending}
            maxLength={160}
            required
            className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="employer-company-website" className="block text-sm font-medium text-ink">
            Website
          </label>
          <input
            id="employer-company-website"
            type="url"
            value={website}
            onChange={(event) => setWebsite(event.target.value)}
            disabled={createCompany.isPending}
            placeholder="https://example.com"
            className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
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
            className="w-full rounded-input border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
          />
        </div>
        {createCompany.isError ? (
          <p className="text-sm text-danger" role="alert">
            {errorMessage(createCompany.error)}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={!companyName.trim() || createCompany.isPending}
          className="min-h-control rounded-button bg-primary px-6 text-sm font-medium text-white disabled:opacity-60"
        >
          {createCompany.isPending ? "Creating…" : "Create company"}
        </button>
      </form>
    </div>
  );
}

function VacanciesPanel({ enabled }: Readonly<{ enabled: boolean }>) {
  const vacanciesQuery = useEmployerVacanciesQuery(enabled);
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
      <p className="text-sm text-secondary">
        Create a company to start posting vacancies.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {vacanciesQuery.isLoading ? (
        <p className="text-sm text-secondary" role="status">
          Loading vacancies…
        </p>
      ) : null}

      {vacanciesQuery.isError ? (
        <div>
          <p className="text-sm text-danger" role="alert">
            {errorMessage(vacanciesQuery.error)}
          </p>
          <button
            type="button"
            onClick={() => void vacanciesQuery.refetch()}
            className="mt-3 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          >
            Try again
          </button>
        </div>
      ) : null}

      {vacanciesQuery.isSuccess && vacanciesQuery.data.length === 0 ? (
        <p className="text-sm text-secondary">No vacancies yet. Create your first opening below.</p>
      ) : null}

      {vacanciesQuery.data && vacanciesQuery.data.length > 0 ? (
        <ul className="space-y-3">
          {vacanciesQuery.data.map((vacancy) => (
            <VacancyCard key={vacancy.id} vacancy={vacancy} />
          ))}
        </ul>
      ) : null}

      <div className="rounded-card border border-border bg-background p-4">
        <p className="text-sm font-medium text-ink">Create vacancy</p>
        <form className="mt-4 space-y-4" onSubmit={onCreateVacancy}>
          <div className="space-y-2">
            <label htmlFor="employer-vacancy-title" className="block text-sm font-medium text-ink">
              Title
            </label>
            <input
              id="employer-vacancy-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={createVacancy.isPending}
              maxLength={200}
              required
              className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
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
              className="w-full rounded-input border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
            />
          </div>
          {createVacancy.isError ? (
            <p className="text-sm text-danger" role="alert">
              {errorMessage(createVacancy.error)}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={!title.trim() || createVacancy.isPending}
            className="min-h-control rounded-button bg-primary px-6 text-sm font-medium text-white disabled:opacity-60"
          >
            {createVacancy.isPending ? "Creating…" : "Create vacancy"}
          </button>
        </form>
      </div>
    </div>
  );
}

export function EmployerSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const companyQuery = useEmployerCompanyQuery(enabled);
  const hasCompany = Boolean(companyQuery.data);

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
        aria-labelledby="employer-section-title"
      >
        <h2 id="employer-section-title" className="text-xl font-semibold text-ink">
          Employer
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          The employer workspace is available only to employer accounts.
        </p>
      </section>
    );
  }

  return (
    <section
      className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
      aria-labelledby="employer-section-title"
    >
      <h2 id="employer-section-title" className="text-xl font-semibold text-ink">
        Employer
      </h2>
      <p className="mt-2 text-sm text-secondary">
        Manage your company profile and job openings.
      </p>

      <div className="mt-6 space-y-8">
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
      </div>
    </section>
  );
}

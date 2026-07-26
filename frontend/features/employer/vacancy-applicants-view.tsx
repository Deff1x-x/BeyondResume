"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, primaryActionClass, secondaryActionClass } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonCard } from "@/components/ui/skeleton";
import { VacancyMatchCard } from "@/features/employer/vacancy-match-card";
import { ShortlistSaveButton } from "@/features/employer/shortlist-save-button";
import { ApiClientError } from "@/lib/api/error";
import type { EmployerApplicant, VacancyMatch } from "@/lib/api/types/employer";
import {
  useApplicantContactQuery,
  useVacancyApplicantsQuery,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Applicants could not be loaded. Please try again.";
}

function toMatch(applicant: EmployerApplicant): VacancyMatch {
  return {
    candidate_id: applicant.candidate_id,
    candidate_name: applicant.candidate_name,
    score: applicant.score,
    required: applicant.required,
    preferred: applicant.preferred
  };
}

function ApplicantContactPanel({
  vacancyId,
  candidateId
}: Readonly<{ vacancyId: string; candidateId: string }>) {
  const contactQuery = useApplicantContactQuery(vacancyId, candidateId, true);

  if (contactQuery.isLoading) {
    return <p className="text-sm text-secondary">Loading contact information…</p>;
  }

  if (contactQuery.isError || !contactQuery.data) {
    return (
      <p className="text-sm text-secondary">
        Contact information is unavailable for this applicant.
      </p>
    );
  }

  const contact = contactQuery.data;
  const rows: Array<{ label: string; value: string | null }> = [
    { label: "Email", value: contact.email },
    { label: "Phone", value: contact.phone },
    { label: "Telegram", value: contact.telegram },
    { label: "LinkedIn", value: contact.linkedin_url },
    { label: "Portfolio", value: contact.portfolio_url },
    { label: "Location", value: contact.location }
  ];

  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {rows.map((row) => (
        <div key={row.label}>
          <dt className="text-xs font-semibold uppercase tracking-wide text-secondary">
            {row.label}
          </dt>
          <dd className="mt-1 break-words text-sm text-ink">
            {row.value?.trim() ? row.value : "Not provided"}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function ApplicantCard({
  applicant,
  vacancyId,
  saved
}: Readonly<{ applicant: EmployerApplicant; vacancyId: string; saved: boolean }>) {
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;

  return (
    <div className="space-y-4">
      <VacancyMatchCard
        match={toMatch(applicant)}
        vacancyId={vacancyId}
        saved={saved}
        pipelineActions={
          <div className="flex flex-wrap gap-2">
            <ShortlistSaveButton
              vacancyId={vacancyId}
              candidateId={applicant.candidate_id}
            />
            <Link href={shortlistHref} className={secondaryActionClass}>
              Open shortlist
            </Link>
          </div>
        }
        notes={
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="primary">Applicant</Badge>
              <span className="text-xs text-secondary">
                Applied {new Date(applicant.applied_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
                Contact Information
              </p>
              <div className="mt-3">
                <ApplicantContactPanel
                  vacancyId={vacancyId}
                  candidateId={applicant.candidate_id}
                />
              </div>
            </div>
          </div>
        }
      />
    </div>
  );
}

export function VacancyApplicantsView({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const applicantsQuery = useVacancyApplicantsQuery(vacancyId, true);
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, true);
  const applicants = applicantsQuery.data?.applicants ?? [];
  const savedIds = new Set(
    (shortlistQuery.data?.entries ?? []).map((entry) => entry.candidate_id)
  );
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;
  const compareHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/compare`;

  return (
    <section
      aria-labelledby={`vacancy-applicants-title-${vacancyId}`}
      className="space-y-6 border-t border-border pt-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Hiring pipeline
          </p>
          <h3
            id={`vacancy-applicants-title-${vacancyId}`}
            className="mt-2 text-lg font-semibold tracking-tight text-ink"
          >
            Applicants
          </h3>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Candidates who applied to this vacancy. Shortlist, interview, and compare from here.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {applicantsQuery.data ? (
            <Badge variant="neutral">
              {applicants.length} {applicants.length === 1 ? "applicant" : "applicants"}
            </Badge>
          ) : null}
          <Link href={shortlistHref} className={secondaryActionClass}>
            Shortlist
          </Link>
          <Link href={compareHref} className={primaryActionClass}>
            Compare
          </Link>
        </div>
      </div>

      {applicantsQuery.isLoading ? (
        <div className="grid gap-4" role="status" aria-label="Loading applicants">
          <SkeletonCard className="min-h-48" />
          <SkeletonCard className="min-h-48" />
        </div>
      ) : null}

      {applicantsQuery.isError ? (
        <EmptyState
          role="alert"
          title="Applicants could not be loaded"
          description={errorMessage(applicantsQuery.error)}
          primaryAction={
            <Button variant="secondary" onClick={() => void applicantsQuery.refetch()}>
              Try again
            </Button>
          }
        />
      ) : null}

      {!applicantsQuery.isLoading && !applicantsQuery.isError && applicants.length === 0 ? (
        <EmptyState
          title="No applicants yet"
          description="When candidates apply to this vacancy, they will appear here. Recommended Candidates remain available for advisory review."
          className="bg-surface py-10"
        />
      ) : null}

      {!applicantsQuery.isLoading && !applicantsQuery.isError && applicants.length > 0 ? (
        <ul className="space-y-4">
          {applicants.map((applicant) => (
            <li key={applicant.application_id}>
              <ApplicantCard
                applicant={applicant}
                vacancyId={vacancyId}
                saved={savedIds.has(applicant.candidate_id)}
              />
            </li>
          ))}
        </ul>
      ) : null}

      {!applicantsQuery.isLoading && applicants.length > 0 ? (
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
            <p className="text-sm text-secondary">
              Use the shortlist to manage hiring stages, then compare shortlisted applicants.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link href={shortlistHref} className={secondaryActionClass}>
                Manage shortlist
              </Link>
              <Link href={compareHref} className={primaryActionClass}>
                Compare applicants
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}

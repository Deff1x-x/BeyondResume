"use client";

import Link from "next/link";

import { ActionCard } from "@/components/ui/action-card";
import { Badge } from "@/components/ui/badge";
import { Button, primaryActionClass, secondaryActionClass } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { SkeletonCard } from "@/components/ui/skeleton";
import { VacancyMatchCard } from "@/features/employer/vacancy-match-card";
import { ShortlistSaveButton } from "@/features/employer/shortlist-save-button";
import { ApiClientError } from "@/lib/api/error";
import type { EmployerApplicant, VacancyMatch } from "@/lib/api/types/employer";
import { cn } from "@/lib/cn";
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
  const questionsHref = `/employer/matches/${encodeURIComponent(applicant.candidate_id)}/interview-questions?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const scorecardHref = `/employer/matches/${encodeURIComponent(applicant.candidate_id)}/scorecard?vacancy_id=${encodeURIComponent(vacancyId)}`;

  return (
    <div className="space-y-4">
      <VacancyMatchCard
        match={toMatch(applicant)}
        vacancyId={vacancyId}
        saved={saved}
        pipelineActions={
          <>
            <ShortlistSaveButton
              vacancyId={vacancyId}
              candidateId={applicant.candidate_id}
              candidateName={applicant.candidate_name}
            />
            <ActionCard
              href={questionsHref}
              icon="message-square-question"
              iconTone="ai"
              title="Interview questions"
              description="AI-generated interview plan"
            />
            <ActionCard
              href={scorecardHref}
              icon="clipboard-check"
              iconTone="primary"
              title="Scorecard"
              description="Evaluate interview"
            />
            <ActionCard
              href={shortlistHref}
              icon="folder-open"
              iconTone="accent"
              title="Open shortlist"
              description="View all shortlisted candidates"
            />
          </>
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
  const shortlistEntries = shortlistQuery.data?.entries;
  const shortlistCount = shortlistEntries?.length;
  const savedIds = new Set((shortlistEntries ?? []).map((entry) => entry.candidate_id));
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;
  const compareHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/compare`;

  return (
    <section
      aria-labelledby={`vacancy-applicants-title-${vacancyId}`}
      className="space-y-6 border-t border-border pt-6"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div className="min-w-0">
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
            Candidates who applied to this vacancy. Shortlist strong fits, then compare with AI.
          </p>
        </div>
        <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:items-center sm:justify-end">
          {applicantsQuery.data ? (
            <Badge variant="neutral" className="w-fit">
              {applicants.length} {applicants.length === 1 ? "applicant" : "applicants"}
            </Badge>
          ) : null}
          <Link
            href={shortlistHref}
            className={cn(
              primaryActionClass,
              "h-auto w-full justify-center gap-2.5 px-5 py-2.5 text-left sm:w-auto sm:min-w-[14.5rem]"
            )}
            aria-label="AI Candidate Comparison"
          >
            <Icon name="spark" className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="min-w-0">
              <span className="block text-sm font-semibold leading-5 tracking-tight">
                AI Candidate Comparison
              </span>
              <span className="mt-0.5 block text-xs font-medium leading-4 text-accent-foreground/75">
                {typeof shortlistCount === "number"
                  ? `${shortlistCount} shortlisted`
                  : "Shortlist and compare candidates"}
              </span>
            </span>
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

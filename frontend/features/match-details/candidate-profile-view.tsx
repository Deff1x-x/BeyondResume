"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { ShortlistNoteEditor } from "@/features/employer/shortlist-note-editor";
import { ShortlistSaveButton } from "@/features/employer/shortlist-save-button";
import { ShortlistStageControl } from "@/features/employer/shortlist-stage-control";
import { EvidenceCard } from "@/features/match-details/evidence-card";
import { EmployerSkillPassport } from "@/features/match-details/employer-skill-passport";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { RoadmapCard } from "@/features/match-details/roadmap-card";
import { SkillsComparisonCard } from "@/features/match-details/skills-comparison-card";
import { ApiClientError } from "@/lib/api/error";
import type { MatchDetailsResponse } from "@/lib/api/types/employer";
import {
  useApplicantContactQuery,
  useMatchDetailsQuery,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

type CandidateProfileViewProps = Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>;

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError ? error.message : "Match details could not be loaded. Please try again.";
}

function sourceLabel(sourceType: string): string {
  if (sourceType === "github_repository") return "GitHub";
  if (sourceType === "resume") return "Résumé";
  return sourceType.replaceAll("_", " ");
}

function MatchDetailsSkeleton() {
  return (
    <div className="space-y-8" role="status" aria-label="Loading candidate profile">
      <SkeletonCard className="min-h-56" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] xl:gap-8">
        <SkeletonCard className="min-h-80" />
        <div className="space-y-5">
          <SkeletonListRow />
          <SkeletonCard className="min-h-40" />
          <SkeletonCard className="min-h-40" />
        </div>
      </div>
    </div>
  );
}

function MatchHero({
  details,
  vacancyId,
  candidateId
}: Readonly<{ details: MatchDetailsResponse; vacancyId: string; candidateId: string }>) {
  const sources = [...new Set(details.evidence.map((item) => item.source_type))];
  const hasApplied = details.has_applied ?? false;
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, true);
  const savedEntry = shortlistQuery.data?.entries.find(
    (entry) => entry.candidate_id === candidateId
  );
  const isSaved = savedEntry !== undefined || (details.is_shortlisted ?? false);
  const questionsHref = `/employer/matches/${encodeURIComponent(candidateId)}/interview-questions?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const scorecardHref = `/employer/matches/${encodeURIComponent(candidateId)}/scorecard?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const showInterviewActions = hasApplied || isSaved;

  return (
    <section
      aria-labelledby="candidate-profile-title"
      className="overflow-hidden rounded-card border border-border bg-surface shadow-card"
    >
      <div className="space-y-6 p-5 sm:p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between lg:gap-8">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">Match evaluated</Badge>
              {isSaved ? <Badge variant="neutral">Shortlisted</Badge> : null}
              {hasApplied ? <Badge variant="primary">Applicant</Badge> : null}
              {sources.map((source) => (
                <Badge key={source} variant="neutral">
                  {sourceLabel(source)}
                </Badge>
              ))}
            </div>
            <div className="mt-4 flex items-start gap-3 sm:gap-4">
              <span
                className="mt-1 inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-surface-subtle text-sm font-semibold tracking-tight text-ink ring-1 ring-border"
                aria-hidden="true"
              >
                {details.candidate.name
                  .trim()
                  .split(/\s+/)
                  .filter(Boolean)
                  .slice(0, 2)
                  .map((part) => part[0]?.toUpperCase() ?? "")
                  .join("") || "?"}
              </span>
              <div className="min-w-0">
                <h1
                  id="candidate-profile-title"
                  className="break-words text-3xl font-semibold tracking-[-0.035em] text-ink sm:text-4xl"
                >
                  {details.candidate.name}
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
                  {details.candidate.headline?.trim() || "Candidate match profile for this vacancy."}
                </p>
                <p className="mt-3 text-sm leading-6 text-secondary">
                  <span className="font-medium text-ink">{details.evidence.length}</span> evidence{" "}
                  {details.evidence.length === 1 ? "source supports" : "sources support"} this evaluation.
                </p>
              </div>
            </div>
          </div>
          <div className="w-full max-w-sm shrink-0 rounded-card border border-border bg-surface-subtle/70 px-5 py-5">
            <div className="flex items-center gap-4">
              <div
                className="flex h-14 w-14 items-center justify-center rounded-full border border-success/20 bg-success/10 text-lg font-semibold tabular-nums text-success"
                aria-label={`Requirement coverage ${details.match.score} percent`}
              >
                {details.match.score}%
              </div>
              <div>
                <p className="text-sm font-medium text-ink">Requirement coverage</p>
                <p className="mt-1 text-sm leading-6 text-secondary">
                  Based on vacancy requirements and skills in the candidate’s Skill Passport
                </p>
              </div>
            </div>
            <div
              className="mt-4 h-1.5 overflow-hidden rounded-full bg-surface"
              role="progressbar"
              aria-label="Requirement coverage"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={details.match.score}
            >
              <div
                className="h-full rounded-full bg-accent"
                style={{ width: `${details.match.score}%` }}
              />
            </div>
          </div>
        </div>

        <div className="space-y-4 border-t border-border pt-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Hiring actions
          </p>
          <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
            <ShortlistSaveButton
              vacancyId={vacancyId}
              candidateId={candidateId}
              candidateName={details.candidate.name}
            />
            {savedEntry ? (
              <ShortlistStageControl
                vacancyId={vacancyId}
                candidateId={candidateId}
                stage={savedEntry.stage}
                candidateLabel={details.candidate.name}
              />
            ) : null}
            {showInterviewActions ? (
              <>
                <Link
                  href={questionsHref}
                  className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink shadow-sm transition duration-200 hover:-translate-y-px hover:border-border-strong hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                >
                  Interview questions
                </Link>
                <Link
                  href={scorecardHref}
                  className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink shadow-sm transition duration-200 hover:-translate-y-px hover:border-border-strong hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
                >
                  Interview scorecard
                </Link>
              </>
            ) : null}
          </div>
        </div>

        {savedEntry ? (
          <div className="space-y-4 border-t border-border pt-6">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
              Private notes
            </p>
            <div className="max-w-2xl">
              <ShortlistNoteEditor
                key={`${vacancyId}:${candidateId}`}
                vacancyId={vacancyId}
                candidateId={candidateId}
                note={savedEntry.note}
                candidateLabel={details.candidate.name}
              />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ContactInformationCard({
  vacancyId,
  candidateId
}: Readonly<{ vacancyId: string; candidateId: string }>) {
  const contactQuery = useApplicantContactQuery(vacancyId, candidateId, true);

  if (contactQuery.isLoading) {
    return <SkeletonCard className="min-h-40" />;
  }

  if (contactQuery.isError || !contactQuery.data) {
    return (
      <Card aria-labelledby="contact-information-title">
        <CardContent className="p-5 sm:p-6">
          <h2 id="contact-information-title" className="text-lg font-semibold text-ink">
            Contact Information
          </h2>
          <p className="mt-3 text-sm text-secondary">
            Contact information is unavailable for this applicant.
          </p>
        </CardContent>
      </Card>
    );
  }

  const contact = contactQuery.data;
  const rows = [
    { label: "Email", value: contact.email },
    { label: "Phone", value: contact.phone },
    { label: "Telegram", value: contact.telegram },
    { label: "LinkedIn", value: contact.linkedin_url },
    { label: "Portfolio", value: contact.portfolio_url },
    { label: "Location", value: contact.location }
  ];

  return (
    <Card aria-labelledby="contact-information-title">
      <CardContent className="p-5 sm:p-6">
        <h2 id="contact-information-title" className="text-lg font-semibold text-ink">
          Contact Information
        </h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          {rows.map(({ label, value }) => (
            <div key={label}>
              <dt className="text-xs font-semibold uppercase tracking-wide text-secondary">
                {label}
              </dt>
              <dd className="mt-1 break-words text-sm text-ink">
                {value?.trim() ? value : "Not provided"}
              </dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}

function MatchSummary({ details }: Readonly<{ details: MatchDetailsResponse }>) {
  const missing = [...details.match.required.missing, ...details.match.preferred.missing];
  return (
    <Card aria-labelledby="match-summary-title">
      <CardContent className="space-y-5 p-5 sm:p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Match summary
          </p>
          <h2 id="match-summary-title" className="mt-2 text-lg font-semibold tracking-tight text-ink">
            Coverage snapshot
          </h2>
        </div>
        <dl className="space-y-4 text-sm">
          <div>
            <dt className="text-secondary">Required skills matched</dt>
            <dd className="mt-1 font-medium text-ink">
              {details.match.required.matched.length} of{" "}
              {details.match.required.matched.length + details.match.required.missing.length}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Evidence signals</dt>
            <dd className="mt-1 font-medium text-ink">{details.evidence.length} linked sources</dd>
          </div>
          <div>
            <dt className="text-secondary">Needs attention</dt>
            <dd className="mt-1 text-ink">
              {missing.length > 0 ? missing.slice(0, 3).join(", ") : "No missing skills reported"}
            </dd>
          </div>
        </dl>
        {details.passport.top_skills.length > 0 ? (
          <div className="border-t border-border pt-5">
            <p className="text-sm font-medium text-ink">Candidate strengths</p>
            <ul className="mt-3 flex flex-wrap gap-2">
              {details.passport.top_skills.map((skill) => (
                <li key={skill}>
                  <Badge variant="primary">{skill}</Badge>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function CandidateProfileView({ candidateId, vacancyId, enabled }: CandidateProfileViewProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);

  const evidenceCountBySkill = useMemo(() => {
    const counts = new Map<string, number>();
    detailsQuery.data?.evidence.forEach((item) => item.skills.forEach((skill) => counts.set(skill, (counts.get(skill) ?? 0) + 1)));
    return counts;
  }, [detailsQuery.data]);

  const backLink = <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2"><Link href="/#employer-vacancies" className="app-link">Employer dashboard</Link><span aria-hidden="true" className="text-muted">/</span><span className="text-secondary">Candidate review</span></nav>;
  if (!enabled) return <EmptyState title="Employer access required" description="Match details are available only to employer accounts." />;
  if (detailsQuery.isLoading) return <div className="space-y-8"><PageHeader title="Candidate match" breadcrumb={backLink} /><MatchDetailsSkeleton /></div>;
  if (detailsQuery.isError || !detailsQuery.data) return <div className="space-y-8"><PageHeader title="Candidate match" breadcrumb={backLink} /><EmptyState role="alert" title="Match details unavailable" description={errorMessage(detailsQuery.error)} className="bg-surface py-10" primaryAction={<Button variant="secondary" onClick={() => void detailsQuery.refetch()}>Try again</Button>} secondaryAction={backLink} /></div>;

  const details = detailsQuery.data;
  const partialGroup = {
    matched: details.match.preferred.matched,
    missing: [] as string[],
    matched_details: details.match.preferred.matched_details
  };
  const missingGroup = {
    matched: [] as string[],
    missing: [...details.match.required.missing, ...details.match.preferred.missing],
    missing_details: [
      ...(details.match.required.missing_details ?? []),
      ...(details.match.preferred.missing_details ?? [])
    ]
  };

  return (
    <div className="space-y-8">
      <div className="text-sm">{backLink}</div>
      <MatchReviewNavigation
        candidateId={candidateId}
        vacancyId={vacancyId}
        active="review"
        hasApplied={details.has_applied}
        isShortlisted={details.is_shortlisted}
      />
      <MatchHero details={details} vacancyId={vacancyId} candidateId={candidateId} />
      {details.has_applied ? (
        <ContactInformationCard vacancyId={vacancyId} candidateId={candidateId} />
      ) : null}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] xl:gap-8">
        <div className="space-y-6">
          <EmployerSkillPassport
            passport={details.passport}
            match={details.match}
            onSelectSkill={setSelectedSkill}
          />
          <SkillsComparisonCard
            title="Skill comparison"
            headingId="skill-comparison-title"
            required={details.match.required}
            partial={partialGroup}
            missing={missingGroup}
            evidenceCountBySkill={evidenceCountBySkill}
            selectedSkill={selectedSkill}
            onSelectSkill={setSelectedSkill}
          />
          <EvidenceCard
            evidence={details.evidence}
            selectedSkill={selectedSkill}
            onClearSkill={() => setSelectedSkill(null)}
          />
        </div>
        <aside className="space-y-6">
          <MatchSummary details={details} />
          <RoadmapCard items={details.roadmap} />
        </aside>
      </div>
    </div>
  );
}

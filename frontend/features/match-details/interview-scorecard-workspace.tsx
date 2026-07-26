"use client";

import Link from "next/link";
import { useEffect, useId, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard } from "@/components/ui/skeleton";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { ApiClientError } from "@/lib/api/error";
import type {
  InterviewRecommendation,
  InterviewScorecard,
  InterviewScorecardInput,
  InterviewScorecardStatus,
  InterviewScorecardSummary
} from "@/lib/api/types/interview-scorecard";
import {
  INTERVIEW_RECOMMENDATION_LABELS,
  INTERVIEW_RECOMMENDATIONS,
  INTERVIEW_SCORECARD_STATUS_LABELS
} from "@/lib/api/types/interview-scorecard";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";
import {
  useInterviewScorecardQuery,
  useSaveInterviewScorecardMutation
} from "@/lib/interview-scorecard/hooks";

const SUMMARY_MAX_LENGTH = 1200;
const NOTES_MAX_LENGTH = 5000;
const SCORE_OPTIONS = [1, 2, 3, 4, 5] as const;
const DIMENSIONS = [
  { key: "technical_competency", label: "Technical Competency" },
  { key: "experience_relevance", label: "Experience Relevance" },
  { key: "communication", label: "Communication" },
  { key: "ownership", label: "Ownership / Accountability" }
] as const;

type EmployerInterviewScorecardWorkspaceProps = Readonly<{
  candidateId: string;
  vacancyId: string;
  enabled: boolean;
}>;

type FormState = {
  technical_competency: number | null;
  experience_relevance: number | null;
  communication: number | null;
  ownership: number | null;
  interview_summary: string;
  interview_notes: string;
  recommendation: InterviewRecommendation | null;
};

function emptyForm(): FormState {
  return {
    technical_competency: null,
    experience_relevance: null,
    communication: null,
    ownership: null,
    interview_summary: "",
    interview_notes: "",
    recommendation: null
  };
}

function formFromScorecard(scorecard: InterviewScorecard): FormState {
  return {
    technical_competency: scorecard.technical_competency,
    experience_relevance: scorecard.experience_relevance,
    communication: scorecard.communication,
    ownership: scorecard.ownership,
    interview_summary: scorecard.interview_summary ?? "",
    interview_notes: scorecard.interview_notes ?? "",
    recommendation: scorecard.recommendation
  };
}

function normalizeOptionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function formToPayload(
  form: FormState,
  status: InterviewScorecardStatus
): InterviewScorecardInput | null {
  if (status === "completed") {
    if (
      form.technical_competency === null ||
      form.experience_relevance === null ||
      form.communication === null ||
      form.ownership === null ||
      form.recommendation === null
    ) {
      return null;
    }
  }

  return {
    status,
    technical_competency: form.technical_competency,
    experience_relevance: form.experience_relevance,
    communication: form.communication,
    ownership: form.ownership,
    interview_summary: normalizeOptionalText(form.interview_summary),
    interview_notes: normalizeOptionalText(form.interview_notes),
    recommendation: form.recommendation
  };
}

function samePayload(
  form: FormState,
  status: InterviewScorecardStatus,
  scorecard: InterviewScorecard | null | undefined
): boolean {
  const payload = formToPayload(form, status);
  if (!payload || !scorecard) {
    return false;
  }
  return (
    payload.status === scorecard.status &&
    payload.technical_competency === scorecard.technical_competency &&
    payload.experience_relevance === scorecard.experience_relevance &&
    payload.communication === scorecard.communication &&
    payload.ownership === scorecard.ownership &&
    payload.interview_summary === scorecard.interview_summary &&
    payload.interview_notes === scorecard.interview_notes &&
    payload.recommendation === scorecard.recommendation
  );
}

function buildLocalSummary(
  form: FormState,
  status: InterviewScorecardStatus
): InterviewScorecardSummary {
  const rated = DIMENSIONS.flatMap((dimension) => {
    const value = form[dimension.key];
    return value === null ? [] : [{ label: dimension.label, score: value }];
  });
  const unanswered = DIMENSIONS.filter((dimension) => form[dimension.key] === null).map(
    (dimension) => dimension.label
  );
  const average =
    rated.length === 0
      ? null
      : Math.round((rated.reduce((sum, item) => sum + item.score, 0) / rated.length) * 100) /
        100;
  const maxScore = rated.length === 0 ? null : Math.max(...rated.map((item) => item.score));
  const minScore = rated.length === 0 ? null : Math.min(...rated.map((item) => item.score));

  return {
    status,
    completed_criteria_count: rated.length,
    total_criteria_count: DIMENSIONS.length,
    average_rating: average,
    strongest_dimensions:
      maxScore === null ? [] : rated.filter((item) => item.score === maxScore).map((item) => item.label),
    weakest_dimensions:
      minScore === null ? [] : rated.filter((item) => item.score === minScore).map((item) => item.label),
    unanswered_dimensions: unanswered,
    recommendation: form.recommendation
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "The interview scorecard could not be saved. Please try again.";
}

function ScoreSelect({
  id,
  label,
  value,
  disabled,
  onChange
}: Readonly<{
  id: string;
  label: string;
  value: number | null;
  disabled: boolean;
  onChange: (value: number) => void;
}>) {
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      <Select
        id={id}
        value={value ?? ""}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value))}
      >
        <option value="" disabled>
          Select 1–5
        </option>
        {SCORE_OPTIONS.map((score) => (
          <option key={score} value={score}>
            {score}
          </option>
        ))}
      </Select>
      <p className="text-xs text-muted">
        1 insufficient · 2 below · 3 meets · 4 strong · 5 exceptional
      </p>
    </div>
  );
}

function ScorecardSummaryPanel({
  summary
}: Readonly<{ summary: InterviewScorecardSummary }>) {
  return (
    <Card aria-labelledby="scorecard-summary-title">
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2 id="scorecard-summary-title" className="text-lg font-semibold text-ink">
            Scorecard summary
          </h2>
          <Badge variant={summary.status === "completed" ? "success" : "neutral"}>
            {INTERVIEW_SCORECARD_STATUS_LABELS[summary.status]}
          </Badge>
        </div>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-secondary">Completed criteria</dt>
            <dd className="mt-1 font-medium text-ink">
              {summary.completed_criteria_count} of {summary.total_criteria_count}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Average rating</dt>
            <dd className="mt-1 font-medium tabular-nums text-ink">
              {summary.average_rating === null ? "—" : summary.average_rating.toFixed(2)}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Strongest</dt>
            <dd className="mt-1 text-ink">
              {summary.strongest_dimensions.length > 0
                ? summary.strongest_dimensions.join(", ")
                : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Weakest</dt>
            <dd className="mt-1 text-ink">
              {summary.weakest_dimensions.length > 0
                ? summary.weakest_dimensions.join(", ")
                : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Unanswered</dt>
            <dd className="mt-1 text-ink">
              {summary.unanswered_dimensions.length > 0
                ? summary.unanswered_dimensions.join(", ")
                : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-secondary">Final recommendation</dt>
            <dd className="mt-1 font-medium text-ink">
              {summary.recommendation
                ? INTERVIEW_RECOMMENDATION_LABELS[summary.recommendation]
                : "Not set"}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function EmployerInterviewScorecardWorkspace({
  candidateId,
  vacancyId,
  enabled
}: EmployerInterviewScorecardWorkspaceProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);
  const scorecardQuery = useInterviewScorecardQuery(vacancyId, candidateId, enabled);
  const saveMutation = useSaveInterviewScorecardMutation(vacancyId, candidateId);
  const formId = useId();
  const [form, setForm] = useState<FormState>(emptyForm);
  const [syncedKey, setSyncedKey] = useState("");
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  const identityKey = `${vacancyId}:${candidateId}`;

  useEffect(() => {
    if (!scorecardQuery.isSuccess) {
      return;
    }
    if (syncedKey === identityKey) {
      return;
    }
    setSyncedKey(identityKey);
    setForm(scorecardQuery.data ? formFromScorecard(scorecardQuery.data) : emptyForm());
    setSavedNotice(null);
  }, [identityKey, scorecardQuery.data, scorecardQuery.isSuccess, syncedKey]);

  const breadcrumb = (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2">
      <Link href="/#employer-vacancies" className="app-link">
        Employer dashboard
      </Link>
      <span aria-hidden="true" className="text-muted">
        /
      </span>
      <Link
        href={`/employer/matches/${encodeURIComponent(candidateId)}?vacancy_id=${encodeURIComponent(vacancyId)}`}
        className="app-link"
      >
        Candidate review
      </Link>
      <span aria-hidden="true" className="text-muted">
        /
      </span>
      <span className="text-secondary">Interview scorecard</span>
    </nav>
  );

  const localSummary = useMemo(
    () =>
      buildLocalSummary(
        form,
        scorecardQuery.data?.status === "completed" ? "completed" : "draft"
      ),
    [form, scorecardQuery.data?.status]
  );

  if (!enabled) {
    return (
      <EmptyState
        title="Employer access required"
        description="Interview scorecards are available only to employer accounts."
      />
    );
  }

  if (detailsQuery.isLoading || scorecardQuery.isLoading) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview Scorecard"
          title="Interview Scorecard"
          description="Record how the interviewer assessed this candidate."
          breadcrumb={breadcrumb}
        />
        <div role="status" aria-label="Loading interview scorecard">
          <SkeletonCard className="min-h-96" />
        </div>
      </div>
    );
  }

  if (detailsQuery.isError || !detailsQuery.data) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview Scorecard"
          title="Interview Scorecard"
          description="Record how the interviewer assessed this candidate."
          breadcrumb={breadcrumb}
        />
        <EmptyState
          role="alert"
          title="Candidate context unavailable"
          description={
            detailsQuery.error instanceof ApiClientError
              ? detailsQuery.error.message
              : "Candidate context could not be loaded. Please try again."
          }
          className="bg-surface py-10"
        />
      </div>
    );
  }

  const details = detailsQuery.data;
  const draftPayload = formToPayload(form, "draft");
  const completePayload = formToPayload(form, "completed");
  const draftUnchanged = samePayload(form, "draft", scorecardQuery.data);
  const completeUnchanged = samePayload(form, "completed", scorecardQuery.data);
  const canSaveDraft = draftPayload !== null && !draftUnchanged && !saveMutation.isPending;
  const canComplete =
    completePayload !== null && !completeUnchanged && !saveMutation.isPending;
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;
  const summary = scorecardQuery.data?.summary ?? localSummary;

  if (scorecardQuery.isError) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview Scorecard"
          title="Interview Scorecard"
          description="Record how the interviewer assessed this candidate."
          breadcrumb={breadcrumb}
        />
        <MatchReviewNavigation
          candidateId={candidateId}
          vacancyId={vacancyId}
          active="scorecard"
          hasApplied={details.has_applied}
          isShortlisted={details.is_shortlisted}
        />
        <EmptyState
          role="alert"
          title="Interview scorecard unavailable"
          description={
            scorecardQuery.error instanceof ApiClientError
              ? scorecardQuery.error.message
              : "The interview scorecard could not be loaded. Please try again."
          }
          className="bg-surface py-10"
          primaryAction={
            <Button type="button" variant="secondary" onClick={() => void scorecardQuery.refetch()}>
              Try again
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Interview Scorecard"
        title="Interview Scorecard"
        description="Manual interviewer assessment for the selected candidate and vacancy. Match Score stays separate."
        breadcrumb={breadcrumb}
      />
      <MatchReviewNavigation
        candidateId={candidateId}
        vacancyId={vacancyId}
        active="scorecard"
        hasApplied={details.has_applied}
        isShortlisted={details.is_shortlisted}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <main>
          <Card>
            <CardContent className="space-y-6 p-5 sm:p-6">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold text-ink">Ratings</h2>
                {scorecardQuery.data ? (
                  <Badge
                    variant={
                      scorecardQuery.data.status === "completed" ? "success" : "neutral"
                    }
                  >
                    {INTERVIEW_SCORECARD_STATUS_LABELS[scorecardQuery.data.status]}
                  </Badge>
                ) : (
                  <Badge variant="neutral">Not started</Badge>
                )}
              </div>
              <p className="text-sm text-secondary">
                Score each dimension from 1 to 5 based on the interview. Incomplete drafts can be
                saved and reopened later.
              </p>

              <div className="grid gap-4 sm:grid-cols-2">
                {DIMENSIONS.map((dimension) => (
                  <ScoreSelect
                    key={dimension.key}
                    id={`${formId}-${dimension.key}`}
                    label={dimension.label}
                    value={form[dimension.key]}
                    disabled={saveMutation.isPending}
                    onChange={(value) => {
                      setSavedNotice(null);
                      setForm((current) => ({ ...current, [dimension.key]: value }));
                    }}
                  />
                ))}
              </div>

              <div className="space-y-2">
                <label htmlFor={`${formId}-summary`} className="block text-sm font-medium text-ink">
                  Interview Summary
                </label>
                <Textarea
                  id={`${formId}-summary`}
                  value={form.interview_summary}
                  rows={3}
                  maxLength={SUMMARY_MAX_LENGTH}
                  disabled={saveMutation.isPending}
                  className="min-h-20"
                  onChange={(event) => {
                    setSavedNotice(null);
                    setForm((current) => ({
                      ...current,
                      interview_summary: event.target.value
                    }));
                  }}
                />
                <p className="text-xs text-muted">
                  {form.interview_summary.length}/{SUMMARY_MAX_LENGTH}
                </p>
              </div>

              <div className="space-y-2">
                <label htmlFor={`${formId}-notes`} className="block text-sm font-medium text-ink">
                  Interview Notes
                </label>
                <Textarea
                  id={`${formId}-notes`}
                  value={form.interview_notes}
                  rows={4}
                  maxLength={NOTES_MAX_LENGTH}
                  disabled={saveMutation.isPending}
                  className="min-h-24"
                  onChange={(event) => {
                    setSavedNotice(null);
                    setForm((current) => ({
                      ...current,
                      interview_notes: event.target.value
                    }));
                  }}
                />
                <p className="text-xs text-muted">
                  Separate from the private shortlist note. {form.interview_notes.length}/
                  {NOTES_MAX_LENGTH}
                </p>
              </div>

              <fieldset className="space-y-3">
                <legend className="text-sm font-medium text-ink">Interviewer Recommendation</legend>
                <div className="grid gap-2 sm:grid-cols-2">
                  {INTERVIEW_RECOMMENDATIONS.map((option) => {
                    const optionId = `${formId}-recommendation-${option}`;
                    return (
                      <label
                        key={option}
                        htmlFor={optionId}
                        className="flex items-center gap-2 rounded-control border border-border bg-surface-subtle/50 px-3 py-2 text-sm text-ink"
                      >
                        <input
                          id={optionId}
                          type="radio"
                          name={`${formId}-recommendation`}
                          value={option}
                          checked={form.recommendation === option}
                          disabled={saveMutation.isPending}
                          onChange={() => {
                            setSavedNotice(null);
                            setForm((current) => ({ ...current, recommendation: option }));
                          }}
                        />
                        <span>{INTERVIEW_RECOMMENDATION_LABELS[option]}</span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <div className="flex flex-wrap items-center gap-3 border-t border-border pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  loading={saveMutation.isPending}
                  disabled={!canSaveDraft}
                  onClick={() => {
                    const nextPayload = formToPayload(form, "draft");
                    if (!nextPayload || saveMutation.isPending) {
                      return;
                    }
                    saveMutation.reset();
                    saveMutation.mutate(nextPayload, {
                      onSuccess: () => {
                        setSavedNotice("Draft scorecard saved.");
                      }
                    });
                  }}
                >
                  {saveMutation.isPending ? "Saving..." : "Save draft"}
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  loading={saveMutation.isPending}
                  disabled={!canComplete}
                  onClick={() => {
                    const nextPayload = formToPayload(form, "completed");
                    if (!nextPayload || saveMutation.isPending) {
                      return;
                    }
                    saveMutation.reset();
                    saveMutation.mutate(nextPayload, {
                      onSuccess: () => {
                        setSavedNotice("Interview scorecard completed.");
                      }
                    });
                  }}
                >
                  {saveMutation.isPending ? "Saving..." : "Complete scorecard"}
                </Button>
                <Link href={shortlistHref} className="app-link text-sm">
                  Open shortlist
                </Link>
              </div>

              {savedNotice && !saveMutation.isError ? (
                <p className="text-sm text-success" role="status">
                  {savedNotice}
                </p>
              ) : null}
              {saveMutation.isError ? (
                <p className="text-sm text-danger" role="alert">
                  {errorMessage(saveMutation.error)}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </main>

        <aside className="space-y-8">
          <ScorecardSummaryPanel summary={summary} />
          <Card aria-labelledby="scorecard-context-title">
            <CardContent className="p-5">
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">
                Selected context
              </p>
              <h2
                id="scorecard-context-title"
                className="mt-2 break-words text-xl font-semibold tracking-tight text-ink"
              >
                {details.candidate.name}
              </h2>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {details.candidate.headline?.trim() ||
                  "Manual interviewer assessment for this vacancy."}
              </p>
              <p className="mt-4 text-sm leading-6 text-secondary">
                Match Score: {details.match.score}%. This scorecard does not change Match Score or
                invent evidence.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

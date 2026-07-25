"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";

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
  InterviewScorecardInput
} from "@/lib/api/types/interview-scorecard";
import {
  INTERVIEW_RECOMMENDATION_LABELS,
  INTERVIEW_RECOMMENDATIONS
} from "@/lib/api/types/interview-scorecard";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";
import {
  useInterviewScorecardQuery,
  useSaveInterviewScorecardMutation
} from "@/lib/interview-scorecard/hooks";

const SUMMARY_MAX_LENGTH = 1200;
const NOTES_MAX_LENGTH = 5000;
const SCORE_OPTIONS = [1, 2, 3, 4, 5] as const;

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

function formToPayload(form: FormState): InterviewScorecardInput | null {
  if (
    form.technical_competency === null ||
    form.experience_relevance === null ||
    form.communication === null ||
    form.ownership === null ||
    form.recommendation === null
  ) {
    return null;
  }
  return {
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
  scorecard: InterviewScorecard | null | undefined
): boolean {
  const payload = formToPayload(form);
  if (!payload || !scorecard) {
    return false;
  }
  return (
    payload.technical_competency === scorecard.technical_competency &&
    payload.experience_relevance === scorecard.experience_relevance &&
    payload.communication === scorecard.communication &&
    payload.ownership === scorecard.ownership &&
    payload.interview_summary === scorecard.interview_summary &&
    payload.interview_notes === scorecard.interview_notes &&
    payload.recommendation === scorecard.recommendation
  );
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
    </div>
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
  const [savedNotice, setSavedNotice] = useState(false);

  const identityKey = `${vacancyId}:${candidateId}`;

  useEffect(() => {
    if (!scorecardQuery.isSuccess) {
      return;
    }
    // Hydrate only when vacancy/candidate identity changes. Refetch must not wipe a dirty draft.
    if (syncedKey === identityKey) {
      return;
    }
    setSyncedKey(identityKey);
    setForm(scorecardQuery.data ? formFromScorecard(scorecardQuery.data) : emptyForm());
    setSavedNotice(false);
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

  if (scorecardQuery.isError) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview Scorecard"
          title="Interview Scorecard"
          description="Record how the interviewer assessed this candidate."
          breadcrumb={breadcrumb}
        />
        <MatchReviewNavigation candidateId={candidateId} vacancyId={vacancyId} active="scorecard" />
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

  const details = detailsQuery.data;
  const payload = formToPayload(form);
  const unchanged = samePayload(form, scorecardQuery.data);
  const canSave = payload !== null && !unchanged && !saveMutation.isPending;
  const shortlistHref = `/employer/vacancies/${encodeURIComponent(vacancyId)}/shortlist`;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Interview Scorecard"
        title="Interview Scorecard"
        description="Manual interviewer assessment for the selected candidate and vacancy."
        breadcrumb={breadcrumb}
      />
      <MatchReviewNavigation candidateId={candidateId} vacancyId={vacancyId} active="scorecard" />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <main>
          <Card>
            <CardContent className="space-y-6 p-5 sm:p-6">
              <div>
                <h2 className="text-lg font-semibold text-ink">Ratings</h2>
                <p className="mt-1 text-sm text-secondary">
                  Score each dimension from 1 to 5 based on the interview.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <ScoreSelect
                  id={`${formId}-technical`}
                  label="Technical Competency"
                  value={form.technical_competency}
                  disabled={saveMutation.isPending}
                  onChange={(value) => {
                    setSavedNotice(false);
                    setForm((current) => ({ ...current, technical_competency: value }));
                  }}
                />
                <ScoreSelect
                  id={`${formId}-experience`}
                  label="Experience Relevance"
                  value={form.experience_relevance}
                  disabled={saveMutation.isPending}
                  onChange={(value) => {
                    setSavedNotice(false);
                    setForm((current) => ({ ...current, experience_relevance: value }));
                  }}
                />
                <ScoreSelect
                  id={`${formId}-communication`}
                  label="Communication"
                  value={form.communication}
                  disabled={saveMutation.isPending}
                  onChange={(value) => {
                    setSavedNotice(false);
                    setForm((current) => ({ ...current, communication: value }));
                  }}
                />
                <ScoreSelect
                  id={`${formId}-ownership`}
                  label="Ownership / Accountability"
                  value={form.ownership}
                  disabled={saveMutation.isPending}
                  onChange={(value) => {
                    setSavedNotice(false);
                    setForm((current) => ({ ...current, ownership: value }));
                  }}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor={`${formId}-summary`} className="block text-sm font-medium text-ink">
                  Interview Summary
                </label>
                <p className="text-sm text-secondary">
                  Concise final assessment from the interview
                </p>
                <Textarea
                  id={`${formId}-summary`}
                  value={form.interview_summary}
                  rows={3}
                  maxLength={SUMMARY_MAX_LENGTH}
                  disabled={saveMutation.isPending}
                  className="min-h-20"
                  onChange={(event) => {
                    setSavedNotice(false);
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
                <p className="text-sm text-secondary">
                  Detailed notes captured during or after the interview
                </p>
                <Textarea
                  id={`${formId}-notes`}
                  value={form.interview_notes}
                  rows={4}
                  maxLength={NOTES_MAX_LENGTH}
                  disabled={saveMutation.isPending}
                  className="min-h-24"
                  onChange={(event) => {
                    setSavedNotice(false);
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
                            setSavedNotice(false);
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
                  variant="primary"
                  loading={saveMutation.isPending}
                  disabled={!canSave}
                  onClick={() => {
                    const nextPayload = formToPayload(form);
                    if (!nextPayload || saveMutation.isPending) {
                      return;
                    }
                    saveMutation.reset();
                    saveMutation.mutate(nextPayload, {
                      onSuccess: () => {
                        setSavedNotice(true);
                      }
                    });
                  }}
                >
                  {saveMutation.isPending ? "Saving..." : "Save"}
                </Button>
                <Link href={shortlistHref} className="app-link text-sm">
                  Open shortlist
                </Link>
              </div>

              {savedNotice && !saveMutation.isError ? (
                <p className="text-sm text-success" role="status">
                  Interview scorecard saved.
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
                This scorecard records interviewer judgment. It does not change pipeline stage or
                replace AI Hiring.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

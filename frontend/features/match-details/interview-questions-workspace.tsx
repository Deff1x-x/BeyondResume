"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon, type IconName } from "@/components/ui/icon";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard } from "@/components/ui/skeleton";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { ApiClientError } from "@/lib/api/error";
import type {
  InterviewQuestion,
  InterviewQuestionCategory,
  InterviewQuestionsResponse
} from "@/lib/api/types/interview-questions";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";
import {
  useInterviewQuestionsQuery,
  useRefreshInterviewQuestionsMutation
} from "@/lib/interview-questions/hooks";

const CATEGORY_ORDER: InterviewQuestionCategory[] = [
  "technical",
  "experience",
  "risk_validation",
  "ownership"
];

const CATEGORY_LABELS: Record<InterviewQuestionCategory, string> = {
  technical: "Technical",
  experience: "Experience",
  risk_validation: "Risk validation",
  ownership: "Ownership"
};

const CATEGORY_ICONS: Record<InterviewQuestionCategory, IconName> = {
  technical: "code",
  experience: "resume",
  risk_validation: "alert",
  ownership: "profile"
};

type InterviewQuestionsWorkspaceProps = Readonly<{
  candidateId: string;
  vacancyId: string;
  enabled: boolean;
}>;

function detailsErrorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "Candidate context could not be loaded. Please try again.";
}

function questionsErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError && error.code === "INTERVIEW_QUESTIONS_UNAVAILABLE") {
    return "Interview questions are temporarily unavailable. Please try again.";
  }
  return error instanceof ApiClientError
    ? error.message
    : "Interview questions are temporarily unavailable. Please try again.";
}

function QuestionsSkeleton() {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] xl:gap-8" role="status" aria-label="Loading interview questions">
      <div className="space-y-8">
        <SkeletonCard className="min-h-72" />
        <SkeletonCard className="min-h-52" />
      </div>
      <SkeletonCard className="min-h-44" />
    </div>
  );
}

function groupQuestions(data: InterviewQuestionsResponse) {
  const groups = new Map<InterviewQuestionCategory, InterviewQuestion[]>();
  for (const category of CATEGORY_ORDER) {
    groups.set(category, []);
  }
  for (const question of data.questions) {
    const bucket = groups.get(question.category);
    if (bucket) {
      bucket.push(question);
    }
  }
  return CATEGORY_ORDER.filter((category) => (groups.get(category)?.length ?? 0) > 0).map(
    (category) => ({
      category,
      label: CATEGORY_LABELS[category],
      questions: groups.get(category) ?? []
    })
  );
}

function QuestionCard({ item }: Readonly<{ item: InterviewQuestion }>) {
  const isGapBased =
    item.category === "risk_validation" ||
    Boolean(item.evidence_basis?.toLowerCase().includes("gap"));

  return (
    <Card>
      <CardContent className="p-5 sm:p-6">
        <p className="break-words text-base font-semibold leading-7 tracking-tight text-ink sm:text-lg sm:leading-8">
          {item.question}
        </p>

        <div className="mt-4 border-t border-border pt-4">
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
            Why this matters
          </p>
          <p className="mt-1.5 break-words text-sm leading-6 text-secondary">{item.reason}</p>
        </div>

        {item.target_skill || item.evidence_basis || isGapBased ? (
          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-border pt-4">
            {item.target_skill ? (
              <div className="flex min-w-0 items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                  Target skill
                </span>
                <Badge variant="primary" title={item.target_skill}>
                  {item.target_skill}
                </Badge>
              </div>
            ) : null}

            {item.evidence_basis ? (
              <div className="flex min-w-0 items-start gap-2">
                <Icon
                  name={isGapBased ? "alert" : "evidence"}
                  className="mt-0.5 h-4 w-4 shrink-0 text-secondary"
                />
                <p className="min-w-0 break-words text-sm leading-6 text-secondary">
                  <span className="mr-1.5 text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                    {isGapBased ? "Gap" : "Evidence"}
                  </span>
                  {item.evidence_basis}
                </p>
              </div>
            ) : isGapBased ? (
              <div className="flex items-center gap-2">
                <Icon name="alert" className="h-4 w-4 shrink-0 text-secondary" />
                <Badge variant="neutral">Gap</Badge>
              </div>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function InterviewQuestionsWorkspace({
  candidateId,
  vacancyId,
  enabled
}: InterviewQuestionsWorkspaceProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);
  const questionsQuery = useInterviewQuestionsQuery(candidateId, vacancyId, enabled);
  const refreshMutation = useRefreshInterviewQuestionsMutation(candidateId, vacancyId);

  const scorecardHref = `/employer/matches/${encodeURIComponent(candidateId)}/scorecard?vacancy_id=${encodeURIComponent(vacancyId)}`;
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
      <span className="text-secondary">Questions</span>
    </nav>
  );

  if (!enabled) {
    return (
      <EmptyState
        title="Employer access required"
        description="Interview questions are available only to employer accounts."
      />
    );
  }

  if (detailsQuery.isLoading || (questionsQuery.isLoading && !questionsQuery.data)) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview preparation"
          title="AI Interview Questions"
          description="Candidate-specific interview questions for the selected vacancy."
          breadcrumb={breadcrumb}
        />
        <QuestionsSkeleton />
      </div>
    );
  }

  if (detailsQuery.isError || !detailsQuery.data) {
    return (
      <div className="space-y-8">
        <PageHeader
          eyebrow="Interview preparation"
          title="AI Interview Questions"
          description="Candidate-specific interview questions for the selected vacancy."
          breadcrumb={breadcrumb}
        />
        <EmptyState
          role="alert"
          title="Candidate context unavailable"
          description={detailsErrorMessage(detailsQuery.error)}
        />
      </div>
    );
  }

  const details = detailsQuery.data;
  const canRegenerate = Boolean(questionsQuery.data);
  const groups = questionsQuery.data ? groupQuestions(questionsQuery.data) : [];
  const questionCount = questionsQuery.data?.questions.length ?? 0;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Interview preparation"
        title="AI Interview Questions"
        description="Candidate-specific interview suggestions for the selected vacancy."
        breadcrumb={breadcrumb}
      />
      <MatchReviewNavigation candidateId={candidateId} vacancyId={vacancyId} active="questions" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] xl:gap-8">
        <main className="space-y-8">
          <Card>
            <CardContent className="flex flex-wrap items-start justify-between gap-5 p-5 sm:p-6">
              <div className="flex min-w-0 gap-3">
                <span
                  aria-hidden="true"
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-card bg-ai/10 text-ai-muted ring-1 ring-ai/20"
                >
                  <Icon name="spark" className="h-[18px] w-[18px]" />
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold tracking-wide text-ai-muted">
                    Interview preparation
                  </p>
                  <p className="mt-1.5 max-w-xl text-sm leading-6 text-secondary">
                    AI-generated interview suggestions. Review each question for job relevance and
                    fairness before use.
                  </p>
                </div>
              </div>
              <Button
                variant="primary"
                disabled={
                  !canRegenerate || refreshMutation.isPending || questionsQuery.isFetching
                }
                onClick={() => {
                  refreshMutation.reset();
                  refreshMutation.mutate();
                }}
              >
                <Icon name="refresh" className="h-4 w-4" />
                {refreshMutation.isPending ? "Regenerating..." : "Regenerate"}
              </Button>
            </CardContent>
          </Card>

          {questionsQuery.isError && !questionsQuery.data ? (
            <div role="status" className="rounded-card border border-border bg-surface p-5 shadow-card sm:p-6">
              <p className="font-medium text-ink">Interview questions are temporarily unavailable.</p>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {questionsErrorMessage(questionsQuery.error)}
              </p>
              <Button
                variant="secondary"
                className="mt-4"
                onClick={() => {
                  void questionsQuery.refetch();
                }}
              >
                <Icon name="refresh" className="h-4 w-4" />
                Try again
              </Button>
            </div>
          ) : null}

          {refreshMutation.isError ? (
            <div role="status" className="rounded-card border border-border bg-surface p-5 shadow-card sm:p-6">
              <p className="font-medium text-ink">Could not regenerate interview questions.</p>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {questionsErrorMessage(refreshMutation.error)} Previous suggestions remain available.
              </p>
            </div>
          ) : null}

          {questionsQuery.data ? (
            <div className="space-y-8">
              {groups.map((group) => (
                <section key={group.category} aria-labelledby={`iq-${group.category}-heading`}>
                  <div className="flex items-center gap-3">
                    <span
                      aria-hidden="true"
                      className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-control bg-primary/10 text-primary"
                    >
                      <Icon name={CATEGORY_ICONS[group.category]} className="h-4 w-4" />
                    </span>
                    <h2
                      id={`iq-${group.category}-heading`}
                      className="text-base font-semibold tracking-tight text-ink"
                    >
                      {group.label}
                    </h2>
                    <span className="text-xs tabular-nums text-secondary">
                      {group.questions.length}
                    </span>
                    <span aria-hidden="true" className="h-px min-w-4 flex-1 bg-border" />
                  </div>
                  <div className="mt-4 space-y-4">
                    {group.questions.map((item, index) => (
                      <QuestionCard key={`${group.category}-${index}-${item.question}`} item={item} />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : null}

          <div>
            <Link
              href={scorecardHref}
              className="inline-flex min-h-control items-center gap-2 rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink shadow-sm transition-colors hover:border-border-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Open Interview Scorecard
              <Icon name="arrow-right" className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </main>

        <aside className="space-y-8">
          <Card aria-labelledby="iq-context-title">
            <CardContent className="p-5 sm:p-6">
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                Candidate
              </p>
              <h2
                id="iq-context-title"
                className="mt-2 break-words text-xl font-semibold tracking-tight text-ink"
              >
                {details.candidate.name}
              </h2>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {details.candidate.headline?.trim() ||
                  "Interview preparation for the selected vacancy."}
              </p>
            </CardContent>
          </Card>

          <Card aria-labelledby="iq-match-title">
            <CardContent className="p-5 sm:p-6">
              <h2
                id="iq-match-title"
                className="text-xs font-medium uppercase tracking-[0.12em] text-secondary"
              >
                Vacancy match
              </h2>
              <p className="mt-3">
                <Badge variant="success">Vacancy match {details.match.score}%</Badge>
              </p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-secondary">Required matched</dt>
                  <dd className="tabular-nums font-medium text-ink">
                    {details.match.required.matched.length}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-secondary">Required missing</dt>
                  <dd className="tabular-nums font-medium text-ink">
                    {details.match.required.missing.length}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-secondary">Questions prepared</dt>
                  <dd className="tabular-nums font-medium text-ink">{questionCount}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5 sm:p-6">
              <p className="text-sm font-medium text-ink">Preparation only</p>
              <p className="mt-2 text-sm leading-6 text-secondary">
                These questions prepare the interview. They do not score the candidate or fill
                the scorecard.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

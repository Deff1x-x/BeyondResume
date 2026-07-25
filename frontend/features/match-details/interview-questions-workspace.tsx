"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
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
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]" role="status" aria-label="Loading interview questions">
      <div className="space-y-6">
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
      <div className="space-y-6">
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
      <div className="space-y-6">
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

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Interview preparation"
        title="AI Interview Questions"
        description="Candidate-specific interview suggestions for the selected vacancy."
        breadcrumb={breadcrumb}
      />
      <MatchReviewNavigation candidateId={candidateId} vacancyId={vacancyId} active="questions" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <main className="space-y-5">
          <Card>
            <CardContent className="flex flex-wrap items-start justify-between gap-4 p-5">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">
                  Interview preparation
                </p>
                <p className="mt-2 text-sm leading-6 text-secondary">
                  AI-generated interview suggestions. Review each question for job relevance and
                  fairness before use.
                </p>
              </div>
              <Button
                size="sm"
                variant="secondary"
                disabled={
                  !canRegenerate || refreshMutation.isPending || questionsQuery.isFetching
                }
                onClick={() => {
                  refreshMutation.reset();
                  refreshMutation.mutate();
                }}
              >
                {refreshMutation.isPending ? "Regenerating..." : "Regenerate"}
              </Button>
            </CardContent>
          </Card>

          {questionsQuery.isError && !questionsQuery.data ? (
            <div role="status" className="rounded-card border border-border bg-surface p-5">
              <p className="font-medium text-ink">Interview questions are temporarily unavailable.</p>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {questionsErrorMessage(questionsQuery.error)}
              </p>
              <Button
                size="sm"
                variant="secondary"
                className="mt-4"
                onClick={() => {
                  void questionsQuery.refetch();
                }}
              >
                Try again
              </Button>
            </div>
          ) : null}

          {refreshMutation.isError ? (
            <div role="status" className="rounded-card border border-border bg-surface p-5">
              <p className="font-medium text-ink">Could not regenerate interview questions.</p>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {questionsErrorMessage(refreshMutation.error)} Previous suggestions remain available.
              </p>
            </div>
          ) : null}

          {questionsQuery.data ? (
            <div className="space-y-6">
              {groupQuestions(questionsQuery.data).map((group) => (
                <section key={group.category} aria-labelledby={`iq-${group.category}-heading`}>
                  <h2
                    id={`iq-${group.category}-heading`}
                    className="text-sm font-semibold uppercase tracking-[0.14em] text-primary"
                  >
                    {group.label}
                  </h2>
                  <div className="mt-3 space-y-4">
                    {group.questions.map((item, index) => (
                      <Card key={`${group.category}-${index}-${item.question}`}>
                        <CardContent className="space-y-3 p-5">
                          <div>
                            <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                              Question
                            </p>
                            <p className="mt-1 text-sm font-medium leading-6 text-ink">
                              {item.question}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs font-medium uppercase tracking-[0.12em] text-secondary">
                              Why ask this
                            </p>
                            <p className="mt-1 text-sm leading-6 text-secondary">{item.reason}</p>
                          </div>
                          {item.target_skill ? (
                            <p className="text-sm text-secondary">
                              Target skill:{" "}
                              <span className="font-medium text-ink">{item.target_skill}</span>
                            </p>
                          ) : null}
                          {item.evidence_basis ? (
                            <p className="text-sm text-secondary">
                              {item.evidence_basis.toLowerCase().includes("gap") ||
                              item.category === "risk_validation"
                                ? "Based on gap"
                                : "Based on evidence"}
                              : {item.evidence_basis}
                            </p>
                          ) : item.category === "risk_validation" ? (
                            <p className="text-sm text-secondary">Based on gap</p>
                          ) : null}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : null}

          <div>
            <Link
              href={scorecardHref}
              className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Open Interview Scorecard
            </Link>
          </div>
        </main>
        <aside className="space-y-6">
          <Card aria-labelledby="iq-context-title">
            <CardContent className="p-5">
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">
                Selected context
              </p>
              <h2 id="iq-context-title" className="mt-2 break-words text-xl font-semibold tracking-tight text-ink">
                {details.candidate.name}
              </h2>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {details.candidate.headline?.trim() ||
                  "Interview preparation for the selected vacancy."}
              </p>
              <div className="mt-5 border-t border-border pt-4">
                <Badge variant="success">Vacancy match {details.match.score}%</Badge>
                <p className="mt-2 text-sm text-secondary">
                  These questions prepare the interview. They do not score the candidate or fill
                  the scorecard.
                </p>
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

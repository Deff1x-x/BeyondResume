import Link from "next/link";

type MatchReviewNavigationProps = Readonly<{
  candidateId: string;
  vacancyId: string;
  active: "review" | "ai" | "questions" | "scorecard";
  hasApplied?: boolean;
  isShortlisted?: boolean;
}>;

export function MatchReviewNavigation({
  candidateId,
  vacancyId,
  active,
  hasApplied = false,
  isShortlisted = false
}: MatchReviewNavigationProps) {
  const query = `vacancy_id=${encodeURIComponent(vacancyId)}`;
  const reviewHref = `/employer/matches/${encodeURIComponent(candidateId)}?${query}`;
  const aiHref = `/employer/matches/${encodeURIComponent(candidateId)}/ai-hiring?${query}`;
  const questionsHref = `/employer/matches/${encodeURIComponent(candidateId)}/interview-questions?${query}`;
  const scorecardHref = `/employer/matches/${encodeURIComponent(candidateId)}/scorecard?${query}`;
  const showInterviewWorkflow = hasApplied || isShortlisted;

  const tabClass = (isActive: boolean) =>
    `rounded-control px-3 py-2 text-sm font-medium transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 ${
      isActive
        ? "bg-surface text-ink shadow-sm"
        : "text-secondary hover:bg-surface/80 hover:text-ink"
    }`;

  return (
    <nav
      aria-label="Candidate workspace"
      className="flex w-fit max-w-full flex-wrap rounded-card border border-border bg-surface-subtle p-1"
    >
      <Link
        href={reviewHref}
        aria-current={active === "review" ? "page" : undefined}
        className={tabClass(active === "review")}
      >
        Overview
      </Link>
      <Link
        href={aiHref}
        aria-current={active === "ai" ? "page" : undefined}
        className={tabClass(active === "ai")}
      >
        AI Hiring
      </Link>
      {showInterviewWorkflow ? (
        <>
          <Link
            href={questionsHref}
            aria-current={active === "questions" ? "page" : undefined}
            className={tabClass(active === "questions")}
          >
            Interview
          </Link>
          <Link
            href={scorecardHref}
            aria-current={active === "scorecard" ? "page" : undefined}
            className={tabClass(active === "scorecard")}
          >
            Scorecard
          </Link>
        </>
      ) : null}
    </nav>
  );
}

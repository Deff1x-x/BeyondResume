import Link from "next/link";

type MatchReviewNavigationProps = Readonly<{
  candidateId: string;
  vacancyId: string;
  active: "review" | "ai";
}>;

export function MatchReviewNavigation({ candidateId, vacancyId, active }: MatchReviewNavigationProps) {
  const query = `vacancy_id=${encodeURIComponent(vacancyId)}`;
  const reviewHref = `/employer/matches/${encodeURIComponent(candidateId)}?${query}`;
  const aiHref = `/employer/matches/${encodeURIComponent(candidateId)}/ai-hiring?${query}`;

  return (
    <nav aria-label="Candidate workspace" className="flex w-fit rounded-xl border border-border bg-surface-subtle p-1">
      <Link href={reviewHref} aria-current={active === "review" ? "page" : undefined} className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 ${active === "review" ? "bg-background text-ink shadow-sm" : "text-secondary hover:bg-background/70 hover:text-ink"}`}>Candidate Review</Link>
      <Link href={aiHref} aria-current={active === "ai" ? "page" : undefined} className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 ${active === "ai" ? "bg-background text-ink shadow-sm" : "text-secondary hover:bg-background/70 hover:text-ink"}`}>AI Hiring</Link>
    </nav>
  );
}

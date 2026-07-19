import type { MatchDetailsCandidate, MatchDetailsPassport } from "@/lib/api/types/employer";

type CandidateSummaryCardProps = Readonly<{
  candidate: MatchDetailsCandidate;
  score: number;
  passport: MatchDetailsPassport;
}>;

export function CandidateSummaryCard({
  candidate,
  score,
  passport
}: CandidateSummaryCardProps) {
  return (
    <aside
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby="candidate-summary-title"
    >
      <p className="text-xs font-medium uppercase tracking-wide text-secondary">Candidate</p>
      <h1 id="candidate-summary-title" className="mt-2 text-2xl font-semibold text-ink">
        {candidate.name}
      </h1>
      <p className="mt-2 text-sm leading-6 text-secondary">
        {candidate.headline?.trim() ? candidate.headline : "No headline provided"}
      </p>

      <div className="mt-8 border-t border-border pt-6">
        <p className="text-xs font-medium uppercase tracking-wide text-secondary">Match score</p>
        <p className="mt-2 text-4xl font-semibold tabular-nums text-ink" aria-label={`Match score ${score}`}>
          {score}
        </p>
        <p className="mt-1 text-sm text-secondary">Out of 100</p>
      </div>

      <div className="mt-8 border-t border-border pt-6">
        <h2 className="text-sm font-medium text-ink">Top skills</h2>
        {passport.top_skills.length === 0 ? (
          <p className="mt-3 text-sm text-secondary">No passport skills yet.</p>
        ) : (
          <ul className="mt-3 flex flex-wrap gap-2" aria-label="Top skills">
            {passport.top_skills.map((skill) => (
              <li
                key={skill}
                className="rounded-button border border-border bg-background px-3 py-1 text-sm text-ink"
              >
                {skill}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

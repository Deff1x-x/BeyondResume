import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
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
    <Card aria-labelledby="candidate-summary-title">
      <CardContent className="space-y-6 p-5 sm:p-6">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-secondary">
            Candidate
          </p>
          <h2
            id="candidate-summary-title"
            className="mt-2 break-words text-xl font-semibold text-ink sm:text-2xl"
          >
            {candidate.name}
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            {candidate.headline?.trim() ? candidate.headline : "No headline provided"}
          </p>
        </div>

        <div className="border-t border-border pt-6">
          <p className="text-xs font-medium uppercase tracking-wide text-secondary">
            Match score
          </p>
          <p
            className="mt-2 text-4xl font-semibold tabular-nums text-ink"
            aria-label={`Match score ${score} out of 100`}
          >
            {score}
          </p>
          <p className="mt-1 text-sm text-secondary">Out of 100</p>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="text-sm font-medium text-ink">Top skills</h3>
          {passport.top_skills.length === 0 ? (
            <p className="mt-3 text-sm text-secondary">No passport skills yet.</p>
          ) : (
            <ul className="mt-3 flex flex-wrap gap-2" aria-label="Top skills">
              {passport.top_skills.map((skill) => (
                <li key={skill} className="min-w-0 max-w-full">
                  <Badge variant="neutral" title={skill}>
                    {skill}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

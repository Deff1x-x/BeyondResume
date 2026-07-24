import Link from "next/link";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import type { VacancyMatch } from "@/lib/api/types/employer";

type VacancyMatchCardProps = Readonly<{
  match: VacancyMatch;
  vacancyId: string;
  saved?: boolean;
  actions?: ReactNode;
}>;

export function VacancyMatchCard({
  match,
  vacancyId,
  saved = false,
  actions
}: VacancyMatchCardProps) {
  const href = `/employer/matches/${match.candidate_id}?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const requiredTotal = match.required.matched.length + match.required.missing.length;
  const preferredTotal = match.preferred.matched.length + match.preferred.missing.length;

  return (
    <li className="rounded-xl border border-border bg-background p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="break-words text-base font-semibold text-ink">{match.candidate_name}</p>
            {saved ? <Badge variant="neutral">Saved</Badge> : null}
          </div>
          <p className="mt-1 text-sm text-secondary">Candidate match for this vacancy</p>
        </div>
        <div className="shrink-0 text-left sm:text-right">
          <p className="text-xl font-semibold tabular-nums text-ink">{match.score}%</p>
          <p className="text-xs font-medium uppercase tracking-wide text-secondary">
            Vacancy match
          </p>
        </div>
      </div>
      <div
        className="mt-4 h-2 overflow-hidden rounded-full bg-surface-subtle"
        role="progressbar"
        aria-label={`${match.candidate_name} vacancy match`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={match.score}
      >
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-200"
          style={{ width: `${match.score}%` }}
        />
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-lg bg-surface-subtle/70 p-3">
          <dt className="text-secondary">Required skills</dt>
          <dd className="mt-1 font-medium text-ink">
            {match.required.matched.length} matched
            {requiredTotal > 0 ? ` of ${requiredTotal}` : ""}
          </dd>
          {match.required.missing.length > 0 ? (
            <p className="mt-1 text-xs leading-5 text-secondary">
              {match.required.missing.length} missing
            </p>
          ) : null}
        </div>
        <div className="rounded-lg bg-surface-subtle/70 p-3">
          <dt className="text-secondary">Preferred skills</dt>
          <dd className="mt-1 font-medium text-ink">
            {match.preferred.matched.length} matched
            {preferredTotal > 0 ? ` of ${preferredTotal}` : ""}
          </dd>
          {match.preferred.missing.length > 0 ? (
            <p className="mt-1 text-xs leading-5 text-secondary">
              {match.preferred.missing.length} missing
            </p>
          ) : null}
        </div>
      </dl>
      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-4">
        <Link
          href={href}
          className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
          aria-label={`Review candidate ${match.candidate_name}`}
        >
          Review candidate
        </Link>
        {actions}
      </div>
    </li>
  );
}

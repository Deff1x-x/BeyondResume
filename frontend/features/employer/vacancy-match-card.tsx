import Link from "next/link";
import { primaryActionClass, secondaryActionClass } from "@/components/ui/button";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import type {
  EmployerCandidateStage,
  VacancyMatch
} from "@/lib/api/types/employer";
import { EMPLOYER_CANDIDATE_STAGE_LABELS } from "@/lib/api/types/employer";

type VacancyMatchCardProps = Readonly<{
  match: VacancyMatch;
  vacancyId: string;
  saved?: boolean;
  selected?: boolean;
  stage?: EmployerCandidateStage;
  /** Dashboard: primary Review. Shortlist: secondary — Compare is primary. */
  reviewVariant?: "primary" | "secondary";
  selection?: Readonly<{
    checked: boolean;
    disabled?: boolean;
    onChange: () => void;
  }>;
  pipelineActions?: ReactNode;
  notes?: ReactNode;
  /** @deprecated Prefer structured slots; kept for backward-compatible callers. */
  actions?: ReactNode;
}>;

function candidateInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return "?";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
}

function stageBadgeVariant(
  stage: EmployerCandidateStage
): "neutral" | "success" | "danger" | "primary" | "warning" {
  if (stage === "hired") {
    return "success";
  }
  if (stage === "rejected") {
    return "danger";
  }
  if (stage === "interview" || stage === "offer") {
    return "primary";
  }
  if (stage === "screening") {
    return "warning";
  }
  return "neutral";
}

function matchBadgeVariant(score: number): "success" | "primary" | "warning" | "neutral" {
  if (score >= 80) {
    return "success";
  }
  if (score >= 60) {
    return "primary";
  }
  if (score >= 40) {
    return "warning";
  }
  return "neutral";
}

export function VacancyMatchCard({
  match,
  vacancyId,
  saved = false,
  selected = false,
  stage,
  reviewVariant = "primary",
  selection,
  pipelineActions,
  notes,
  actions
}: VacancyMatchCardProps) {
  const href = `/employer/matches/${match.candidate_id}?vacancy_id=${encodeURIComponent(vacancyId)}`;
  const requiredTotal = match.required.matched.length + match.required.missing.length;
  const preferredTotal = match.preferred.matched.length + match.preferred.missing.length;
  const isSelected = selected || selection?.checked === true;
  const hasStructuredChrome =
    selection != null || pipelineActions != null || notes != null;

  const reviewClassName =
    reviewVariant === "primary" ? primaryActionClass : secondaryActionClass;

  return (
    <li
      className={cn(
        "rounded-card border bg-surface p-5 shadow-card transition duration-200 sm:p-6",
        isSelected
          ? "border-primary/40 bg-primary/[0.03] ring-1 ring-primary/15"
          : "border-border hover:border-border-strong hover:shadow-card-hover"
      )}
    >
      {/* Candidate header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className={cn(
              "mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold tracking-tight",
              isSelected
                ? "bg-primary/15 text-primary ring-1 ring-primary/20"
                : "bg-surface-subtle text-ink ring-1 ring-border"
            )}
            aria-hidden="true"
          >
            {candidateInitials(match.candidate_name)}
          </span>
          <div className="min-w-0 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="break-words text-base font-semibold tracking-tight text-ink">
                {match.candidate_name}
              </p>
              {saved ? <Badge variant="neutral">Saved</Badge> : null}
              {stage ? (
                <Badge variant={stageBadgeVariant(stage)}>
                  {EMPLOYER_CANDIDATE_STAGE_LABELS[stage]}
                </Badge>
              ) : null}
            </div>
            <p className="text-sm leading-6 text-secondary">
              Candidate match for this vacancy
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
          <Badge variant={matchBadgeVariant(match.score)} className="tabular-nums">
            {match.score}% match
          </Badge>
          <p className="text-xl font-semibold tabular-nums tracking-tight text-ink">
            {match.score}%
          </p>
        </div>
      </div>

      {/* Match summary */}
      <div className="mt-6 space-y-4 border-t border-border pt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
          Match summary
        </p>
        <div
          className="h-1.5 overflow-hidden rounded-full bg-surface-subtle"
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
        <dl className="grid gap-4 sm:grid-cols-2">
          <div className="flex min-h-[5.25rem] flex-col rounded-card border border-border bg-surface-subtle/70 p-4">
            <dt className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">
              Required skills
            </dt>
            <dd className="mt-2 text-sm font-medium text-ink">
              {match.required.matched.length} matched
              {requiredTotal > 0 ? ` of ${requiredTotal}` : ""}
            </dd>
            {match.required.missing.length > 0 ? (
              <p className="mt-1 text-xs leading-5 text-secondary">
                {match.required.missing.length} missing
              </p>
            ) : requiredTotal > 0 ? (
              <p className="mt-1 text-xs leading-5 text-success">All covered</p>
            ) : (
              <p className="mt-1 text-xs leading-5 text-muted">None listed</p>
            )}
          </div>
          <div className="flex min-h-[5.25rem] flex-col rounded-card border border-border bg-surface-subtle/70 p-4">
            <dt className="text-xs font-medium uppercase tracking-[0.1em] text-secondary">
              Preferred skills
            </dt>
            <dd className="mt-2 text-sm font-medium text-ink">
              {match.preferred.matched.length} matched
              {preferredTotal > 0 ? ` of ${preferredTotal}` : ""}
            </dd>
            {match.preferred.missing.length > 0 ? (
              <p className="mt-1 text-xs leading-5 text-secondary">
                {match.preferred.missing.length} missing
              </p>
            ) : preferredTotal > 0 ? (
              <p className="mt-1 text-xs leading-5 text-success">All covered</p>
            ) : (
              <p className="mt-1 text-xs leading-5 text-muted">None listed</p>
            )}
          </div>
        </dl>
      </div>

      {/* Actions */}
      <div className="mt-6 space-y-4 border-t border-border pt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
          Actions
        </p>

        {selection ? (
          <label
            className={cn(
              "flex min-h-control cursor-pointer items-center gap-3 rounded-card border px-4 py-3 text-sm transition duration-200",
              selection.disabled && !selection.checked
                ? "cursor-not-allowed opacity-60"
                : "hover:border-border-strong",
              selection.checked
                ? "border-primary/35 bg-primary/10 font-medium text-primary"
                : "border-border bg-surface-subtle/70 text-ink"
            )}
          >
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-border text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed"
              checked={selection.checked}
              disabled={selection.disabled}
              aria-label={`Select ${match.candidate_name} for comparison`}
              onChange={selection.onChange}
            />
            <span className="min-w-0">
              <span className="block">Select for comparison</span>
              <span className="mt-0.5 block text-xs font-normal text-secondary">
                {selection.checked
                  ? "Included in Compare selection"
                  : "Adds this card to the compare set"}
              </span>
            </span>
          </label>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={href}
            className={reviewClassName}
            aria-label={`Review candidate ${match.candidate_name}`}
          >
            Review candidate
          </Link>
          {pipelineActions ? (
            <div className="flex min-h-control flex-wrap items-center gap-3">
              {pipelineActions}
            </div>
          ) : null}
          {!hasStructuredChrome ? actions : null}
        </div>
      </div>

      {/* Private notes */}
      {notes ? (
        <div className="mt-6 space-y-4 border-t border-border pt-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">
            Private notes
          </p>
          {notes}
        </div>
      ) : null}
    </li>
  );
}

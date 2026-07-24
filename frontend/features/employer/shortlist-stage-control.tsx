"use client";

import { Badge } from "@/components/ui/badge";
import { controlClassName } from "@/components/ui/input";
import { ApiClientError } from "@/lib/api/error";
import type { EmployerCandidateStage } from "@/lib/api/types/employer";
import {
  EMPLOYER_CANDIDATE_STAGE_LABELS,
  EMPLOYER_CANDIDATE_STAGES
} from "@/lib/api/types/employer";
import { useUpdateEmployerShortlistStage } from "@/lib/employer/hooks";
import { cn } from "@/lib/cn";

type ShortlistStageControlProps = Readonly<{
  vacancyId: string;
  candidateId: string;
  stage: EmployerCandidateStage;
  candidateLabel?: string;
}>;

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "The hiring stage could not be updated. Please try again.";
}

function stageBadgeVariant(
  stage: EmployerCandidateStage
): "neutral" | "success" | "danger" {
  if (stage === "hired") {
    return "success";
  }
  if (stage === "rejected") {
    return "danger";
  }
  return "neutral";
}

export function ShortlistStageControl({
  vacancyId,
  candidateId,
  stage,
  candidateLabel
}: ShortlistStageControlProps) {
  const updateMutation = useUpdateEmployerShortlistStage(vacancyId);
  const pendingThis =
    updateMutation.isPending && updateMutation.variables?.candidateId === candidateId;
  const labelTarget = candidateLabel?.trim() || "candidate";

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={stageBadgeVariant(stage)}>
          {EMPLOYER_CANDIDATE_STAGE_LABELS[stage]}
        </Badge>
        <select
          value={stage}
          disabled={pendingThis}
          aria-busy={pendingThis || undefined}
          aria-label={`Hiring stage for ${labelTarget}`}
          className={cn(controlClassName, "min-h-control max-w-[12rem] px-3")}
          onChange={(event) => {
            const nextStage = event.target.value as EmployerCandidateStage;
            if (nextStage === stage || pendingThis) {
              return;
            }
            updateMutation.reset();
            updateMutation.mutate({ candidateId, stage: nextStage });
          }}
        >
          {EMPLOYER_CANDIDATE_STAGES.map((option) => (
            <option key={option} value={option}>
              {EMPLOYER_CANDIDATE_STAGE_LABELS[option]}
            </option>
          ))}
        </select>
      </div>
      {updateMutation.isError &&
      updateMutation.variables?.candidateId === candidateId ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(updateMutation.error)}
        </p>
      ) : null}
    </div>
  );
}

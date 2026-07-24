"use client";

import { Button } from "@/components/ui/button";
import { ApiClientError } from "@/lib/api/error";
import {
  useRemoveCandidateFromShortlist,
  useSaveCandidateToShortlist,
  useVacancyShortlistQuery
} from "@/lib/employer/hooks";

type ShortlistSaveButtonProps = Readonly<{
  vacancyId: string;
  candidateId: string;
  candidateName?: string;
}>;

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "The shortlist request failed. Please try again.";
}

export function ShortlistSaveButton({
  vacancyId,
  candidateId,
  candidateName
}: ShortlistSaveButtonProps) {
  const shortlistQuery = useVacancyShortlistQuery(vacancyId, true);
  const saveMutation = useSaveCandidateToShortlist(vacancyId);
  const removeMutation = useRemoveCandidateFromShortlist(vacancyId);

  const isSaved =
    shortlistQuery.data?.entries.some((entry) => entry.candidate_id === candidateId) ??
    false;
  const savingThis =
    saveMutation.isPending && saveMutation.variables === candidateId;
  const removingThis =
    removeMutation.isPending && removeMutation.variables === candidateId;
  const isBusy = savingThis || removingThis;
  const stateUnknown = shortlistQuery.isLoading || shortlistQuery.isError;
  const labelTarget = candidateName?.trim() || "candidate";

  const error =
    (shortlistQuery.isError ? shortlistQuery.error : null) ??
    (saveMutation.isError ? saveMutation.error : null) ??
    (removeMutation.isError ? removeMutation.error : null);

  return (
    <div className="space-y-2">
      {isSaved ? (
        <Button
          type="button"
          variant="secondary"
          loading={removingThis}
          disabled={isBusy || stateUnknown}
          aria-label={`Remove ${labelTarget} from shortlist`}
          onClick={() => {
            if (isBusy) {
              return;
            }
            removeMutation.reset();
            saveMutation.reset();
            removeMutation.mutate(candidateId);
          }}
        >
          {removingThis ? "Removing..." : "Saved"}
        </Button>
      ) : (
        <Button
          type="button"
          variant="primary"
          loading={savingThis}
          disabled={isBusy || stateUnknown}
          aria-label={`Save ${labelTarget} to shortlist`}
          onClick={() => {
            if (isBusy) {
              return;
            }
            saveMutation.reset();
            removeMutation.reset();
            saveMutation.mutate(candidateId);
          }}
        >
          {savingThis ? "Saving..." : "Save"}
        </Button>
      )}
      {error ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}

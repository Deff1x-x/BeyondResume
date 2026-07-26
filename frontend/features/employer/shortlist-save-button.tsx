"use client";

import { ActionCard } from "@/components/ui/action-card";
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
    <>
      {isSaved ? (
        <>
          <ActionCard
            status
            variant="success"
            icon="bookmark-check"
            title="Shortlisted"
            description="Saved to vacancy shortlist"
            aria-label={`${labelTarget} is shortlisted`}
          />
          <ActionCard
            variant="destructive"
            icon="trash-2"
            title={removingThis ? "Removing..." : "Remove from shortlist"}
            description="Remove candidate from shortlist"
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
          />
        </>
      ) : (
        <ActionCard
          variant="secondary"
          icon="bookmark-plus"
          iconTone="accent"
          title={savingThis ? "Adding..." : "Add to shortlist"}
          description="Save candidate to this vacancy"
          loading={savingThis}
          disabled={isBusy || stateUnknown}
          aria-label={`Add ${labelTarget} to shortlist`}
          onClick={() => {
            if (isBusy) {
              return;
            }
            saveMutation.reset();
            removeMutation.reset();
            saveMutation.mutate(candidateId);
          }}
        />
      )}
      {error ? (
        <p className="col-span-full text-sm text-danger" role="alert">
          {errorMessage(error)}
        </p>
      ) : null}
    </>
  );
}

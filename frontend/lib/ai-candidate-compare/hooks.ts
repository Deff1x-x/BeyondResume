"use client";

import { useEffect } from "react";
import { useMutation } from "@tanstack/react-query";

import { postVacancyAiCompare } from "@/lib/api/ai-candidate-compare";
import type { AiCandidateCompareResponse } from "@/lib/api/types/ai-candidate-compare";

export function aiCandidateCompareMutationKey(vacancyId: string, candidateIds: string[]) {
  return [
    "employer",
    "vacancy",
    vacancyId,
    "ai-compare",
    ...[...candidateIds].sort()
  ] as const;
}

export function useAiCandidateCompareMutation(vacancyId: string, candidateIds: string[]) {
  const selectionKey = candidateIds.join(",");
  const mutation = useMutation({
    mutationKey: aiCandidateCompareMutationKey(vacancyId, candidateIds),
    mutationFn: (): Promise<AiCandidateCompareResponse> =>
      postVacancyAiCompare(vacancyId, { candidate_ids: candidateIds }),
    retry: false
  });

  useEffect(() => {
    mutation.reset();
    // Reset only when compare identity changes so a failed retry does not wipe prior UI via auto-fire.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional identity guard
  }, [vacancyId, selectionKey]);

  return mutation;
}

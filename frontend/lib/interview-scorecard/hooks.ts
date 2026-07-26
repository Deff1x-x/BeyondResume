"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getInterviewScorecard, putInterviewScorecard } from "@/lib/api/interview-scorecard";
import { ApiClientError } from "@/lib/api/error";
import type {
  InterviewScorecard,
  InterviewScorecardInput
} from "@/lib/api/types/interview-scorecard";
import { vacancyShortlistQueryKey } from "@/lib/employer/hooks";

export function interviewScorecardQueryKey(vacancyId: string, candidateId: string) {
  return ["employer", "vacancy", vacancyId, "scorecard", candidateId] as const;
}

export function isScorecardNotFoundError(error: unknown): boolean {
  return (
    error instanceof ApiClientError &&
    error.status === 404 &&
    error.code === "SCORECARD_NOT_FOUND"
  );
}

export function useInterviewScorecardQuery(
  vacancyId: string,
  candidateId: string,
  enabled: boolean
) {
  return useQuery({
    queryKey: interviewScorecardQueryKey(vacancyId, candidateId),
    queryFn: async (): Promise<InterviewScorecard | null> => {
      try {
        return await getInterviewScorecard(vacancyId, candidateId);
      } catch (error) {
        if (isScorecardNotFoundError(error)) {
          return null;
        }
        throw error;
      }
    },
    enabled,
    staleTime: 30_000,
    retry: false
  });
}

export function useSaveInterviewScorecardMutation(vacancyId: string, candidateId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InterviewScorecardInput) =>
      putInterviewScorecard(vacancyId, candidateId, payload),
    onSuccess: (scorecard) => {
      queryClient.setQueryData<InterviewScorecard | null>(
        interviewScorecardQueryKey(vacancyId, candidateId),
        scorecard
      );
      void queryClient.invalidateQueries({
        queryKey: vacancyShortlistQueryKey(vacancyId)
      });
    }
  });
}

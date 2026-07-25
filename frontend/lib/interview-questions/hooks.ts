"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getInterviewQuestions,
  refreshInterviewQuestions
} from "@/lib/api/interview-questions";
import type { InterviewQuestionsResponse } from "@/lib/api/types/interview-questions";

export function interviewQuestionsQueryKey(candidateId: string, vacancyId: string) {
  return ["employer", "matches", candidateId, vacancyId, "interview-questions"] as const;
}

export function useInterviewQuestionsQuery(
  candidateId: string,
  vacancyId: string,
  enabled: boolean
) {
  return useQuery({
    queryKey: interviewQuestionsQueryKey(candidateId, vacancyId),
    queryFn: () => getInterviewQuestions(candidateId, vacancyId),
    enabled,
    staleTime: 60_000,
    retry: false
  });
}

type RefreshPayload = {
  candidateId: string;
  vacancyId: string;
  data: InterviewQuestionsResponse;
};

export function useRefreshInterviewQuestionsMutation(candidateId: string, vacancyId: string) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: [...interviewQuestionsQueryKey(candidateId, vacancyId), "refresh"],
    mutationFn: async (): Promise<RefreshPayload> => {
      const data = await refreshInterviewQuestions(candidateId, vacancyId);
      return { candidateId, vacancyId, data };
    },
    onSuccess: (payload) => {
      queryClient.setQueryData(
        interviewQuestionsQueryKey(payload.candidateId, payload.vacancyId),
        payload.data
      );
    }
  });

  useEffect(() => {
    mutation.reset();
    // Reset only on identity change so regenerate error/pending state does not bleed.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional identity guard
  }, [candidateId, vacancyId]);

  return mutation;
}

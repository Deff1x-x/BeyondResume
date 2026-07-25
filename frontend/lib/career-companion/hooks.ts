"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  generateCareerCompanionPlan,
  getCareerCompanionPlan,
  patchCareerCompanionAction,
  postCareerCompanionChat,
  refreshCareerCompanionFromEvidence
} from "@/lib/api/career-companion";
import type { CareerCompanionGenerateRequest } from "@/lib/api/types/career-companion";
import { ApiClientError } from "@/lib/api/error";

export const careerCompanionQueryKey = ["candidate", "career-companion"] as const;

export function useCareerCompanionQuery(enabled: boolean) {
  return useQuery({
    queryKey: careerCompanionQueryKey,
    queryFn: getCareerCompanionPlan,
    enabled,
    staleTime: 30_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    }
  });
}

export function useGenerateCareerCompanion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CareerCompanionGenerateRequest) => generateCareerCompanionPlan(payload),
    onSuccess: (plan) => {
      queryClient.setQueryData(careerCompanionQueryKey, plan);
    }
  });
}

export function usePatchCareerCompanionAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      actionId,
      status
    }: {
      actionId: string;
      status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed";
    }) => patchCareerCompanionAction(actionId, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: careerCompanionQueryKey });
    }
  });
}

export function useCareerCompanionChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (message: string) => postCareerCompanionChat(message),
    onSuccess: (response) => {
      if (response.plan) {
        queryClient.setQueryData(careerCompanionQueryKey, response.plan);
      } else {
        void queryClient.invalidateQueries({ queryKey: careerCompanionQueryKey });
      }
    }
  });
}

export function useRefreshCareerCompanion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshCareerCompanionFromEvidence,
    onSuccess: (plan) => {
      queryClient.setQueryData(careerCompanionQueryKey, plan);
    }
  });
}

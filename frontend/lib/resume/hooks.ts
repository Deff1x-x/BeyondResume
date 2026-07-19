"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getCurrentResume,
  retryResumeProcessing,
  uploadResume
} from "@/lib/api/resume";
import { candidateDashboardQueryKey } from "@/lib/dashboard/hooks";
import { jobQueryKey, useJobQuery } from "@/lib/jobs/hooks";
import { roadmapQueryKey } from "@/lib/roadmap/hooks";
import { skillPassportQueryKey } from "@/lib/skill-passport/hooks";

export const currentResumeQueryKey = ["candidate", "resume", "current"] as const;

export function useCurrentResumeQuery(enabled: boolean) {
  return useQuery({
    queryKey: currentResumeQueryKey,
    queryFn: getCurrentResume,
    enabled,
    staleTime: 10_000,
    gcTime: 300_000
  });
}

export function useUploadResumeMutation() {
  return useMutation({
    mutationFn: (file: File) => uploadResume(file)
  });
}

export function useRetryResumeMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryResumeProcessing,
    onSuccess: (job) => {
      queryClient.setQueryData(jobQueryKey(job.id), job);
    }
  });
}

export function useResumeJobQuery(jobId: string | null) {
  const queryClient = useQueryClient();
  const query = useJobQuery(jobId);

  useEffect(() => {
    if (query.data?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: currentResumeQueryKey });
      void queryClient.invalidateQueries({ queryKey: skillPassportQueryKey });
      void queryClient.invalidateQueries({ queryKey: roadmapQueryKey });
      void queryClient.invalidateQueries({ queryKey: candidateDashboardQueryKey });
    }
  }, [query.data?.status, queryClient]);

  return query;
}

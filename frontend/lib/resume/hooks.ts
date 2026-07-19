"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getCurrentResume,
  getResumeJob,
  retryResumeProcessing,
  uploadResume
} from "@/lib/api/resume";
import type { JobStatus } from "@/lib/api/types/jobs";

export const currentResumeQueryKey = ["candidate", "resume", "current"] as const;

export function resumeJobQueryKey(jobId: string | null) {
  return ["jobs", jobId] as const;
}

export function isTerminalJobStatus(status: JobStatus | undefined): boolean {
  return (
    status === "completed" ||
    status === "failed" ||
    status === "cancelled" ||
    status === "expired"
  );
}

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
      queryClient.setQueryData(resumeJobQueryKey(job.id), job);
    }
  });
}

export function useResumeJobQuery(jobId: string | null) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: resumeJobQueryKey(jobId),
    queryFn: () => {
      if (jobId === null) {
        throw new Error("A job ID is required");
      }

      return getResumeJob(jobId);
    },
    enabled: jobId !== null,
    staleTime: 0,
    gcTime: 300_000,
    refetchInterval: (currentQuery) =>
      currentQuery.state.error || isTerminalJobStatus(currentQuery.state.data?.status)
        ? false
        : 2_000
  });

  useEffect(() => {
    if (query.data?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: currentResumeQueryKey });
    }
  }, [query.data?.status, queryClient]);

  return query;
}

"use client";

import { useQuery } from "@tanstack/react-query";

import { getJob } from "@/lib/api/jobs";
import type { JobStatus } from "@/lib/api/types/jobs";

export function jobQueryKey(jobId: string | null) {
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

/**
 * Canonical polling query for any background job: 2000ms interval,
 * stops on terminal status, query error, or missing job id.
 */
export function useJobQuery(jobId: string | null) {
  return useQuery({
    queryKey: jobQueryKey(jobId),
    queryFn: () => {
      if (jobId === null) {
        throw new Error("A job ID is required");
      }

      return getJob(jobId);
    },
    enabled: jobId !== null,
    staleTime: 0,
    gcTime: 300_000,
    refetchInterval: (currentQuery) =>
      currentQuery.state.error || isTerminalJobStatus(currentQuery.state.data?.status)
        ? false
        : 2_000
  });
}

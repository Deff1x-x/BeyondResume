"use client";

import { useQuery } from "@tanstack/react-query";

import { getCandidateDashboard } from "@/lib/api/dashboard";

export const candidateDashboardQueryKey = ["candidate", "dashboard"] as const;

export function useCandidateDashboardQuery(enabled: boolean) {
  return useQuery({
    queryKey: candidateDashboardQueryKey,
    queryFn: getCandidateDashboard,
    enabled,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

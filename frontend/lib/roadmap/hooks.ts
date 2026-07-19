"use client";

import { useQuery } from "@tanstack/react-query";

import { getRoadmap } from "@/lib/api/roadmap";

export const roadmapQueryKey = ["candidate", "roadmap"] as const;

export function useRoadmapQuery(enabled: boolean) {
  return useQuery({
    queryKey: roadmapQueryKey,
    queryFn: getRoadmap,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

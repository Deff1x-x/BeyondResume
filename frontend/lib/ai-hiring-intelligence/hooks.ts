"use client";

import { useQuery } from "@tanstack/react-query";
import { getAiHiringIntelligence } from "@/lib/api/ai-hiring-intelligence";

export function aiHiringIntelligenceQueryKey(candidateId: string, vacancyId: string) {
  return ["employer", "matches", candidateId, vacancyId, "ai-hiring-intelligence"] as const;
}
export function useAiHiringIntelligenceQuery(candidateId: string, vacancyId: string, enabled: boolean) {
  return useQuery({ queryKey: aiHiringIntelligenceQueryKey(candidateId, vacancyId), queryFn: () => getAiHiringIntelligence(candidateId, vacancyId), enabled, staleTime: 60_000, retry: false });
}

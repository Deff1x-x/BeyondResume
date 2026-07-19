"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { listCandidateEvidence } from "@/lib/api/evidence";
import type { EvidenceHubQueryParams } from "@/lib/api/types/evidence";

export const evidenceHubQueryKeyRoot = ["candidate", "evidence"] as const;

export function evidenceHubQueryKey(params: EvidenceHubQueryParams) {
  return [
    ...evidenceHubQueryKeyRoot,
    params.source_type ?? "",
    params.skill ?? "",
    params.search ?? "",
    params.limit ?? 20,
    params.offset ?? 0
  ] as const;
}

export function useEvidenceHubQuery(params: EvidenceHubQueryParams, enabled: boolean) {
  return useQuery({
    queryKey: evidenceHubQueryKey(params),
    queryFn: () => listCandidateEvidence(params),
    enabled,
    staleTime: 15_000,
    gcTime: 300_000,
    placeholderData: keepPreviousData
  });
}

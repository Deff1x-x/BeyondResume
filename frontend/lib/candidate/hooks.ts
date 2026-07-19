"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getCandidateProfile, updateCandidateProfile } from "@/lib/api/candidate";
import type {
  CandidateProfilePatchRequest,
  CandidateProfileResponse
} from "@/lib/api/types/candidate";

export const candidateProfileQueryKey = ["candidate", "profile"] as const;

export function useCandidateProfileQuery(enabled: boolean) {
  return useQuery({
    queryKey: candidateProfileQueryKey,
    queryFn: getCandidateProfile,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

export function useUpdateCandidateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (patch: CandidateProfilePatchRequest) => updateCandidateProfile(patch),
    onSuccess: (profile: CandidateProfileResponse) => {
      queryClient.setQueryData(candidateProfileQueryKey, profile);
    }
  });
}

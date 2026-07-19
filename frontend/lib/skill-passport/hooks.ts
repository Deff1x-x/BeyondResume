"use client";

import { useQuery } from "@tanstack/react-query";

import { getSkillPassport } from "@/lib/api/skill-passport";

export const skillPassportQueryKey = ["candidate", "skill-passport"] as const;

export function useSkillPassportQuery(enabled: boolean) {
  return useQuery({
    queryKey: skillPassportQueryKey,
    queryFn: getSkillPassport,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

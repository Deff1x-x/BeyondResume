import { useQuery } from "@tanstack/react-query";

import { getCandidateVacancy, listCandidateVacancies } from "@/lib/api/candidate-vacancies";

export const candidateVacanciesQueryKey = ["candidate", "vacancies"] as const;

export function useCandidateVacanciesQuery(enabled: boolean) {
  return useQuery({
    queryKey: candidateVacanciesQueryKey,
    queryFn: listCandidateVacancies,
    enabled,
    staleTime: 30_000
  });
}

export function useCandidateVacancyQuery(vacancyId: string, enabled: boolean) {
  return useQuery({
    queryKey: [...candidateVacanciesQueryKey, vacancyId],
    queryFn: () => getCandidateVacancy(vacancyId),
    enabled: enabled && vacancyId.length > 0,
    staleTime: 30_000
  });
}

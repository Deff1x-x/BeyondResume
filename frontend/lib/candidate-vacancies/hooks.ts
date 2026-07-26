import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  applyToVacancy,
  getCandidateVacancy,
  listCandidateVacancies,
  withdrawApplication
} from "@/lib/api/candidate-vacancies";

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

export function useApplyToVacancy(vacancyId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => applyToVacancy(vacancyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: candidateVacanciesQueryKey });
    }
  });
}

export function useWithdrawApplication(vacancyId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => withdrawApplication(vacancyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: candidateVacanciesQueryKey });
    }
  });
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addVacancyRequirement,
  createEmployerCompany,
  createEmployerVacancy,
  deleteVacancyRequirement,
  generateMatchExplanation,
  getEmployerCompany,
  getEmployerVacancy,
  getMatchDetails,
  listEmployerSkills,
  listEmployerVacancies,
  listVacancyMatches,
  listVacancyRequirements
} from "@/lib/api/employer";
import type {
  EmployerCompanyCreateRequest,
  VacancyCreateRequest,
  VacancyRequirementCreateRequest
} from "@/lib/api/types/employer";
import { ApiClientError } from "@/lib/api/error";

export const employerCompanyQueryKey = ["employer", "company"] as const;
export const employerVacanciesQueryKey = ["employer", "vacancies"] as const;
export const employerSkillsQueryKey = ["employer", "skills"] as const;

export function employerVacancyQueryKey(vacancyId: string) {
  return ["employer", "vacancy", vacancyId] as const;
}

export function vacancyRequirementsQueryKey(vacancyId: string) {
  return ["employer", "vacancy", vacancyId, "requirements"] as const;
}

export function vacancyMatchesQueryKey(vacancyId: string) {
  return ["employer", "vacancy", vacancyId, "matches"] as const;
}

export function useEmployerCompanyQuery(enabled: boolean) {
  return useQuery({
    queryKey: employerCompanyQueryKey,
    queryFn: getEmployerCompany,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 404) {
        return false;
      }
      return failureCount < 1;
    }
  });
}

export function useCreateEmployerCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: EmployerCompanyCreateRequest) => createEmployerCompany(request),
    onSuccess: (company) => {
      queryClient.setQueryData(employerCompanyQueryKey, company);
    }
  });
}

export function useEmployerVacanciesQuery(enabled: boolean) {
  return useQuery({
    queryKey: employerVacanciesQueryKey,
    queryFn: listEmployerVacancies,
    enabled,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

export function useCreateEmployerVacancy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: VacancyCreateRequest) => createEmployerVacancy(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: employerVacanciesQueryKey });
    }
  });
}

export function useEmployerVacancyQuery(vacancyId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: employerVacancyQueryKey(vacancyId ?? ""),
    queryFn: () => {
      if (vacancyId === null) {
        throw new Error("A vacancy ID is required");
      }
      return getEmployerVacancy(vacancyId);
    },
    enabled: enabled && vacancyId !== null,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

export function useEmployerSkillsQuery(enabled: boolean) {
  return useQuery({
    queryKey: employerSkillsQueryKey,
    queryFn: listEmployerSkills,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

export function useVacancyRequirementsQuery(vacancyId: string, enabled: boolean) {
  return useQuery({
    queryKey: vacancyRequirementsQueryKey(vacancyId),
    queryFn: () => listVacancyRequirements(vacancyId),
    enabled,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

export function useAddVacancyRequirement(vacancyId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: VacancyRequirementCreateRequest) =>
      addVacancyRequirement(vacancyId, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: vacancyRequirementsQueryKey(vacancyId)
      });
      void queryClient.invalidateQueries({ queryKey: vacancyMatchesQueryKey(vacancyId) });
    }
  });
}

export function useDeleteVacancyRequirement(vacancyId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requirementId: string) => deleteVacancyRequirement(vacancyId, requirementId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: vacancyRequirementsQueryKey(vacancyId)
      });
      void queryClient.invalidateQueries({ queryKey: vacancyMatchesQueryKey(vacancyId) });
    }
  });
}

export function useVacancyMatchesQuery(vacancyId: string, enabled: boolean) {
  return useQuery({
    queryKey: vacancyMatchesQueryKey(vacancyId),
    queryFn: () => listVacancyMatches(vacancyId),
    enabled,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

export function matchDetailsQueryKey(candidateId: string, vacancyId: string) {
  return ["employer", "matches", candidateId, vacancyId] as const;
}

export function matchExplanationQueryKey(candidateId: string, vacancyId: string) {
  return ["employer", "matches", candidateId, vacancyId, "explanation"] as const;
}

export function useMatchDetailsQuery(
  candidateId: string | null,
  vacancyId: string | null,
  enabled: boolean
) {
  return useQuery({
    queryKey: matchDetailsQueryKey(candidateId ?? "", vacancyId ?? ""),
    queryFn: () => {
      if (candidateId === null || vacancyId === null) {
        throw new Error("Candidate and vacancy IDs are required");
      }
      return getMatchDetails(candidateId, vacancyId);
    },
    enabled: enabled && candidateId !== null && vacancyId !== null,
    staleTime: 30_000,
    gcTime: 300_000
  });
}

export function useMatchExplanationQuery(
  candidateId: string | null,
  vacancyId: string | null,
  enabled: boolean
) {
  return useQuery({
    queryKey: matchExplanationQueryKey(candidateId ?? "", vacancyId ?? ""),
    queryFn: () => {
      if (candidateId === null || vacancyId === null) {
        throw new Error("Candidate and vacancy IDs are required");
      }
      return generateMatchExplanation(candidateId, vacancyId);
    },
    enabled: enabled && candidateId !== null && vacancyId !== null,
    staleTime: 300_000,
    gcTime: 600_000,
    retry: false
  });
}

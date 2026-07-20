import { apiRequest } from "@/lib/api/client";
import type {
  EmployerCompany,
  EmployerCompanyCreateRequest,
  AiMatchExplanation,
  MatchDetailsResponse,
  SkillOption,
  Vacancy,
  VacancyCreateRequest,
  VacancyMatchesResponse,
  VacancyRequirement,
  VacancyRequirementCreateRequest
} from "@/lib/api/types/employer";

export function getEmployerCompany(): Promise<EmployerCompany> {
  return apiRequest<EmployerCompany>("/employer/company");
}

export function createEmployerCompany(
  request: EmployerCompanyCreateRequest
): Promise<EmployerCompany> {
  return apiRequest<EmployerCompany>("/employer/company", {
    method: "POST",
    body: request
  });
}

export function listEmployerVacancies(): Promise<Vacancy[]> {
  return apiRequest<Vacancy[]>("/employer/vacancies");
}

export function createEmployerVacancy(request: VacancyCreateRequest): Promise<Vacancy> {
  return apiRequest<Vacancy>("/employer/vacancies", {
    method: "POST",
    body: request
  });
}

export function getEmployerVacancy(vacancyId: string): Promise<Vacancy> {
  return apiRequest<Vacancy>(`/employer/vacancies/${vacancyId}`);
}

export function listEmployerSkills(): Promise<SkillOption[]> {
  return apiRequest<SkillOption[]>("/employer/skills");
}

export function listVacancyRequirements(vacancyId: string): Promise<VacancyRequirement[]> {
  return apiRequest<VacancyRequirement[]>(`/employer/vacancies/${vacancyId}/requirements`);
}

export function addVacancyRequirement(
  vacancyId: string,
  request: VacancyRequirementCreateRequest
): Promise<VacancyRequirement> {
  return apiRequest<VacancyRequirement>(`/employer/vacancies/${vacancyId}/requirements`, {
    method: "POST",
    body: request
  });
}

export function deleteVacancyRequirement(
  vacancyId: string,
  requirementId: string
): Promise<void> {
  return apiRequest<void>(`/employer/vacancies/${vacancyId}/requirements/${requirementId}`, {
    method: "DELETE"
  });
}

export function listVacancyMatches(vacancyId: string): Promise<VacancyMatchesResponse> {
  return apiRequest<VacancyMatchesResponse>(`/employer/vacancies/${vacancyId}/matches`);
}

export function getMatchDetails(
  candidateId: string,
  vacancyId: string
): Promise<MatchDetailsResponse> {
  const params = new URLSearchParams({ vacancy_id: vacancyId });
  return apiRequest<MatchDetailsResponse>(
    `/employer/matches/${candidateId}?${params.toString()}`
  );
}

export function generateMatchExplanation(
  candidateId: string,
  vacancyId: string
): Promise<AiMatchExplanation> {
  const params = new URLSearchParams({ vacancy_id: vacancyId });
  return apiRequest<AiMatchExplanation>(
    `/employer/matches/${candidateId}/explanation?${params.toString()}`,
    { method: "POST" }
  );
}

import { apiRequest } from "@/lib/api/client";
import type { CandidateVacancy, CandidateVacancyDetail } from "@/lib/api/types/candidate-vacancies";

export function listCandidateVacancies(): Promise<CandidateVacancy[]> {
  return apiRequest<CandidateVacancy[]>("/candidate/vacancies");
}

export function getCandidateVacancy(vacancyId: string): Promise<CandidateVacancyDetail> {
  return apiRequest<CandidateVacancyDetail>(`/candidate/vacancies/${vacancyId}`);
}

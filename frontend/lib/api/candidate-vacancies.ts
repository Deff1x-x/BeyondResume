import { apiRequest } from "@/lib/api/client";
import type {
  CandidateApplication,
  CandidateVacancy,
  CandidateVacancyDetail
} from "@/lib/api/types/candidate-vacancies";

export function listCandidateVacancies(): Promise<CandidateVacancy[]> {
  return apiRequest<CandidateVacancy[]>("/candidate/vacancies");
}

export function getCandidateVacancy(vacancyId: string): Promise<CandidateVacancyDetail> {
  return apiRequest<CandidateVacancyDetail>(`/candidate/vacancies/${vacancyId}`);
}

export function applyToVacancy(vacancyId: string): Promise<CandidateApplication> {
  return apiRequest<CandidateApplication>(`/candidate/vacancies/${vacancyId}/application`, {
    method: "POST"
  });
}

export function withdrawApplication(vacancyId: string): Promise<CandidateApplication> {
  return apiRequest<CandidateApplication>(`/candidate/vacancies/${vacancyId}/application`, {
    method: "PATCH",
    body: { status: "withdrawn" }
  });
}

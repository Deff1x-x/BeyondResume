import { apiRequest } from "@/lib/api/client";
import type { InterviewQuestionsResponse } from "@/lib/api/types/interview-questions";

export function getInterviewQuestions(candidateId: string, vacancyId: string) {
  const params = new URLSearchParams({ vacancy_id: vacancyId });
  return apiRequest<InterviewQuestionsResponse>(
    `/employer/matches/${candidateId}/interview-questions?${params.toString()}`
  );
}

export function refreshInterviewQuestions(candidateId: string, vacancyId: string) {
  const params = new URLSearchParams({ vacancy_id: vacancyId, refresh: "true" });
  return apiRequest<InterviewQuestionsResponse>(
    `/employer/matches/${candidateId}/interview-questions?${params.toString()}`
  );
}

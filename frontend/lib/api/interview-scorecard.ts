import { apiRequest } from "@/lib/api/client";
import type {
  InterviewScorecard,
  InterviewScorecardInput
} from "@/lib/api/types/interview-scorecard";

export function getInterviewScorecard(
  vacancyId: string,
  candidateId: string
): Promise<InterviewScorecard> {
  return apiRequest<InterviewScorecard>(
    `/employer/vacancies/${vacancyId}/scorecards/${candidateId}`
  );
}

export function putInterviewScorecard(
  vacancyId: string,
  candidateId: string,
  payload: InterviewScorecardInput
): Promise<InterviewScorecard> {
  return apiRequest<InterviewScorecard>(
    `/employer/vacancies/${vacancyId}/scorecards/${candidateId}`,
    {
      method: "PUT",
      body: payload
    }
  );
}

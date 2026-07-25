import { apiRequest } from "@/lib/api/client";
import type {
  AiCandidateCompareRequest,
  AiCandidateCompareResponse
} from "@/lib/api/types/ai-candidate-compare";

export function postVacancyAiCompare(
  vacancyId: string,
  request: AiCandidateCompareRequest
): Promise<AiCandidateCompareResponse> {
  return apiRequest<AiCandidateCompareResponse>(
    `/employer/vacancies/${encodeURIComponent(vacancyId)}/ai-compare`,
    {
      method: "POST",
      body: request
    }
  );
}

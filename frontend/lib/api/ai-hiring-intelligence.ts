import { apiRequest } from "@/lib/api/client";
import type { AiHiringIntelligence } from "@/lib/api/types/ai-hiring-intelligence";

export function getAiHiringIntelligence(candidateId: string, vacancyId: string) {
  const params = new URLSearchParams({ vacancy_id: vacancyId });
  return apiRequest<AiHiringIntelligence>(`/employer/matches/${candidateId}/ai-hiring-intelligence?${params.toString()}`);
}

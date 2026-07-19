import { apiRequest } from "@/lib/api/client";
import type { CandidateDashboardResponse } from "@/lib/api/types/dashboard";

export function getCandidateDashboard(): Promise<CandidateDashboardResponse> {
  return apiRequest<CandidateDashboardResponse>("/candidate/dashboard");
}

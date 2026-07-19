import { apiRequest } from "@/lib/api/client";
import type { JobPollingResponse } from "@/lib/api/types/jobs";

export function getJob(jobId: string): Promise<JobPollingResponse> {
  return apiRequest<JobPollingResponse>(`/jobs/${jobId}`);
}

import { apiRequest } from "@/lib/api/client";
import type { JobPollingResponse } from "@/lib/api/types/jobs";
import type {
  ResumeResponse,
  ResumeUploadAcceptedResponse
} from "@/lib/api/types/resume";

export function uploadResume(file: File): Promise<ResumeUploadAcceptedResponse> {
  const body = new FormData();
  body.append("file", file);

  return apiRequest<ResumeUploadAcceptedResponse>("/candidate/resumes", {
    method: "POST",
    body
  });
}

export function getCurrentResume(): Promise<ResumeResponse> {
  return apiRequest<ResumeResponse>("/candidate/resumes");
}

export function retryResumeProcessing(): Promise<JobPollingResponse> {
  return apiRequest<JobPollingResponse>("/candidate/resume/retry", {
    method: "POST"
  });
}

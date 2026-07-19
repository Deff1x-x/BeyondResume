import { apiRequest } from "@/lib/api/client";
import type {
  CandidateProfilePatchRequest,
  CandidateProfileResponse
} from "@/lib/api/types/candidate";

export function getCandidateProfile(): Promise<CandidateProfileResponse> {
  return apiRequest<CandidateProfileResponse>("/candidate/profile");
}

export function updateCandidateProfile(
  patch: CandidateProfilePatchRequest
): Promise<CandidateProfileResponse> {
  return apiRequest<CandidateProfileResponse>("/candidate/profile", {
    method: "PATCH",
    body: patch
  });
}

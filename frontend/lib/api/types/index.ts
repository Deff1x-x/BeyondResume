export type {
  LoginRequest,
  PublicUserResponse,
  RegisterRequest,
  RegisterSuccessResponse,
  Role,
  TokenResponse,
  VerificationRequiredResponse
} from "@/lib/api/types/auth";

export type {
  CandidateProfilePatchRequest,
  CandidateProfileResponse,
  OnboardingStatus
} from "@/lib/api/types/candidate";

export type {
  ApiErrorDetail,
  ApiErrorEnvelope,
  ApiErrorPayload
} from "@/lib/api/types/error";

export type { JobPollingResponse, JobStatus } from "@/lib/api/types/jobs";

export type {
  ResumeResponse,
  ResumeStatus,
  ResumeUploadAcceptedResponse
} from "@/lib/api/types/resume";

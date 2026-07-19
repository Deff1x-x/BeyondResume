import type { ResumeStatus } from "@/lib/api/types/resume";

export type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

export type JobType =
  | "resume_parse"
  | "profile_analysis"
  | "github_scan"
  | "passport_generation"
  | "vacancy_normalization"
  | "match_calculation"
  | "assessment_review"
  | "roadmap_generation"
  | "export_generation"
  | "webhook_delivery";

export type JobPollingResponse = {
  id: string;
  job_type: JobType;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  resume_status: ResumeStatus | null;
  retry_available: boolean;
};

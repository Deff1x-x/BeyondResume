import type { ResumeStatus } from "@/lib/api/types/resume";

export type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

export type JobPollingResponse = {
  id: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  resume_status: ResumeStatus;
  retry_available: boolean;
};

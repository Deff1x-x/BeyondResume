export type ResumeUploadAcceptedResponse = {
  resume_id: string;
  job_id: string;
};

export type ResumeStatus = "uploaded" | "parsed" | "failed";

export type ResumeResponse = {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: ResumeStatus;
  uploaded_at: string;
};

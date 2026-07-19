export type ResumeUploadAcceptedResponse = {
  resume_id: string;
  job_id: string;
};

export type ResumeStatus = "uploaded" | "parsed" | "failed";

export type ResumeEvidenceSkill = {
  name: string;
  category: string;
  extraction_method: string;
  evidence_confidence: number;
};

export type ResumeResponse = {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: ResumeStatus;
  uploaded_at: string;
  parsed_at: string | null;
  extracted_text_length: number | null;
  evidence_id: string | null;
  skills: ResumeEvidenceSkill[];
};

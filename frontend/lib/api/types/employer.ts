export type EmployerCompany = {
  id: string;
  company_name: string;
  website: string | null;
  description: string | null;
  created_at: string;
};

export type EmployerCompanyCreateRequest = {
  company_name: string;
  website?: string | null;
  description?: string | null;
};

export type EmployerCompanyUpdateRequest = {
  company_name?: string;
  website?: string | null;
  description?: string | null;
};

export type VacancyStatus = "draft" | "open" | "closed";

export type Vacancy = {
  id: string;
  title: string;
  description: string | null;
  status: VacancyStatus;
  created_at: string;
};

export type VacancyCreateRequest = {
  title: string;
  description?: string | null;
  status?: VacancyStatus;
};

export type VacancyRequirementType = "required" | "preferred";

export type VacancyRequirement = {
  id: string;
  skill_id: string;
  skill_name: string;
  skill_category: string;
  requirement_type: VacancyRequirementType;
};

export type VacancyRequirementCreateRequest = {
  skill_id: string;
  requirement_type: VacancyRequirementType;
};

export type SkillOption = {
  id: string;
  name: string;
  category: string;
};

export type SignalSummary = {
  category: string;
};

export type MatchedSkillEvidence = {
  id: string;
  source_type: string;
  title: string | null;
  verification_status: string | null;
  ownership_status: string | null;
  evidence_confidence: number;
  /** Absent on older responses; treat as empty. */
  signal_summaries?: SignalSummary[];
};

export type MatchedSkillDetails = {
  skill_id: string;
  skill_name: string;
  evidence: MatchedSkillEvidence[];
};

export type EvidenceSuggestion = {
  category: string;
};

export type MissingSkillDetails = {
  skill_id: string;
  skill_name: string;
  evidence_suggestions: EvidenceSuggestion[];
};

export type MatchSkillGroup = {
  matched: string[];
  missing: string[];
  /** Absent on older responses / list endpoint; treat as empty. */
  matched_details?: MatchedSkillDetails[];
  /** Absent on older responses / list endpoint; treat as empty. */
  missing_details?: MissingSkillDetails[];
};

export type VacancyMatch = {
  candidate_id: string;
  candidate_name: string;
  score: number;
  required: MatchSkillGroup;
  preferred: MatchSkillGroup;
};

export type VacancyMatchesResponse = {
  matches: VacancyMatch[];
};

export type MatchDetailsCandidate = {
  id: string;
  name: string;
  headline: string | null;
  avatar: string | null;
};

export type MatchDetailsMatch = {
  score: number;
  required: MatchSkillGroup;
  preferred: MatchSkillGroup;
};

export type MatchDetailsPassport = {
  top_skills: string[];
  /** Optional while independently deployed backends may still return the legacy summary. */
  skills?: MatchDetailsPassportSkill[];
};

export type MatchDetailsPassportSkill = {
  name: string;
  evidence_confidence: number;
  evidence_count: number;
  source_types: string[];
};

export type MatchDetailsEvidence = {
  source_type: string;
  title: string | null;
  /** Present on current backends; optional for older fixtures. */
  verification_status?: string | null;
  /** Present on current backends; optional for older fixtures. */
  ownership_status?: string | null;
  skills: string[];
};

export type MatchDetailsRoadmapItem = {
  id: string;
  title: string;
  reason: string;
  priority: "high" | "medium" | "low";
  missing_skills: string[];
  related_skills: string[];
};

export type MatchDetailsResponse = {
  candidate: MatchDetailsCandidate;
  match: MatchDetailsMatch;
  passport: MatchDetailsPassport;
  evidence: MatchDetailsEvidence[];
  roadmap: MatchDetailsRoadmapItem[];
  has_applied?: boolean;
};

export type ApplicationStatus = "applied" | "withdrawn";

export type EmployerApplicant = {
  application_id: string;
  candidate_id: string;
  candidate_name: string;
  status: ApplicationStatus;
  applied_at: string;
  score: number;
  required: MatchSkillGroup;
  preferred: MatchSkillGroup;
};

export type EmployerApplicantsResponse = {
  applicants: EmployerApplicant[];
};

export type ApplicantContact = {
  email: string;
  phone: string | null;
  telegram: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  location: string | null;
};

export type AiMatchExplanation = {
  summary: string;
  strengths: string[];
  gaps: string[];
  next_steps: string[];
};

export type EmployerCandidateStage =
  | "shortlisted"
  | "screening"
  | "interview"
  | "offer"
  | "hired"
  | "rejected";

export const EMPLOYER_CANDIDATE_STAGES = [
  "shortlisted",
  "screening",
  "interview",
  "offer",
  "hired",
  "rejected"
] as const satisfies readonly EmployerCandidateStage[];

export const EMPLOYER_CANDIDATE_STAGE_LABELS: Record<EmployerCandidateStage, string> = {
  shortlisted: "Shortlisted",
  screening: "Screening",
  interview: "Interview",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected"
};

export type EmployerShortlistEntry = {
  id: string;
  vacancy_id: string;
  candidate_id: string;
  stage: EmployerCandidateStage;
  note: string | null;
  created_at: string;
  updated_at: string;
};

export type EmployerShortlistNoteUpdateRequest = {
  note: string | null;
};

export type EmployerShortlistResponse = {
  entries: EmployerShortlistEntry[];
};

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

export type MatchSkillGroup = {
  matched: string[];
  missing: string[];
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
};

export type AiMatchExplanation = {
  summary: string;
  strengths: string[];
  gaps: string[];
  next_steps: string[];
};

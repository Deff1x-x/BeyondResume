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

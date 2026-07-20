export type MatchSkillGroup = {
  matched: string[];
  missing: string[];
};

export type CandidateVacancyMatch = {
  score: number;
  required: MatchSkillGroup;
  preferred: MatchSkillGroup;
};

export type VacancyRoadmapItem = {
  id: string;
  title: string;
  reason: string;
  priority: "high" | "medium" | "low";
  missing_skills: string[];
  related_skills: string[];
};

export type CandidateVacancy = {
  id: string;
  title: string;
  company_name: string;
  description: string | null;
  created_at: string;
  match: CandidateVacancyMatch;
  required_skills: string[];
  preferred_skills: string[];
};

export type CandidateVacancyDetail = CandidateVacancy & {
  roadmap: VacancyRoadmapItem[];
};

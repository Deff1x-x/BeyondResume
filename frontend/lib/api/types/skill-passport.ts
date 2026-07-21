export type SkillPassportEvidence = {
  id: string;
  title: string | null;
  description: string | null;
  source_type: string;
  source_reference: string | null;
  evidence_confidence: number;
};

export type SkillPassportSkill = {
  id: string;
  name: string;
  category: string;
  evidence_confidence: number;
  evidence_count: number;
  evidence: SkillPassportEvidence[];
  github_repositories: { repository_name: string; repository_url: string; evidence_count: number; repository_confidence: number }[];
};

export type SkillPassportResponse = {
  skills: SkillPassportSkill[];
  total_skills: number;
  total_evidence: number;
};

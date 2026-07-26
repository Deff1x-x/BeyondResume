export type AiCandidateCompareGenerationMode = "live" | "mock";
export type AiCandidateCompareConfidence = "low" | "medium" | "high";

export type GroundedInsight = {
  text: string;
  fact_refs: string[];
};

export type GroundedQuestion = {
  question: string;
  candidate_ids: string[];
  fact_refs: string[];
};

export type CandidateAssessment = {
  candidate_id: string;
  strengths: GroundedInsight[];
  risks: GroundedInsight[];
};

export type HiringRecommendation = {
  why_leads: GroundedInsight[];
  main_risk: GroundedInsight;
  interview_focus: GroundedInsight[];
  alternative_outcome: GroundedInsight;
};

export type AiCandidateCompareRequest = {
  candidate_ids: string[];
};

export type AiCandidateCompareResponse = {
  vacancy_id: string;
  candidate_ids: string[];
  generation_mode: AiCandidateCompareGenerationMode;
  summary: string;
  candidate_assessments: CandidateAssessment[];
  key_differences: GroundedInsight[];
  interview_focus_questions: GroundedQuestion[];
  recommended_candidate_id: string;
  hiring_recommendation: HiringRecommendation;
  confidence: AiCandidateCompareConfidence;
  uncertainties: GroundedInsight[];
};

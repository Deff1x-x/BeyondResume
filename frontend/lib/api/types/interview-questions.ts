export type InterviewQuestionCategory =
  | "technical"
  | "experience"
  | "risk_validation"
  | "ownership";

export type InterviewQuestion = {
  category: InterviewQuestionCategory;
  question: string;
  reason: string;
  target_skill: string | null;
  evidence_basis: string | null;
};

export type InterviewQuestionsResponse = {
  questions: InterviewQuestion[];
};

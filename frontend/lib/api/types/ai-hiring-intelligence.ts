export type AiHiringIntelligence = {
  verdict: { technical_interview_recommendation: string; confidence: number; summary: string; strengths: string[]; concerns: string[] };
  interview_questions: { skill: string; difficulty: "easy" | "medium" | "hard"; question: string; reason: string }[];
};

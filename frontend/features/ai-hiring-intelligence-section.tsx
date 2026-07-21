"use client";

import { Card, CardContent } from "@/components/ui/card";
import { SkeletonCard } from "@/components/ui/skeleton";
import { useAiHiringIntelligenceQuery } from "@/lib/ai-hiring-intelligence/hooks";

export function AiHiringIntelligenceSection({ candidateId, vacancyId, enabled }: Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>) {
  const query = useAiHiringIntelligenceQuery(candidateId, vacancyId, enabled);
  if (query.isLoading) return <div role="status"><p className="text-sm text-secondary">Generating AI analysis...</p><SkeletonCard /></div>;
  if (query.isError || !query.data) return <p role="status" className="text-sm text-secondary">AI analysis is temporarily unavailable.</p>;
  const { verdict, interview_questions: questions } = query.data;
  return <div className="space-y-5"><Card><CardContent className="p-5"><h2 className="text-lg font-semibold text-ink">Technical Interview Verdict</h2><p className="mt-1 text-sm text-secondary">Evidence-based technical interview recommendation</p><p className="mt-3 text-sm font-medium text-primary">{recommendationLabel(verdict.technical_interview_recommendation)}</p><p className="mt-1 text-sm text-secondary">{verdict.confidence}% confidence</p><p className="mt-4 text-sm leading-6 text-secondary">{verdict.summary}</p><List title="Strengths" items={verdict.strengths} /><List title="Concerns" items={verdict.concerns} /></CardContent></Card><Card><CardContent className="p-5"><h2 className="text-lg font-semibold text-ink">Interview Questions</h2>{questions.map((item) => <div key={`${item.skill}-${item.question}`} className="mt-4 border-t border-border pt-4"><p className="text-sm font-medium text-ink">{item.skill} · {item.difficulty}</p><p className="mt-2 text-sm text-secondary">{item.question}</p><p className="mt-2 text-xs text-muted">Reason: {item.reason}</p></div>)}</CardContent></Card></div>;
}
function List({ title, items }: Readonly<{ title: string; items: string[] }>) { return items.length ? <div className="mt-4"><p className="text-sm font-medium text-ink">{title}</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-secondary">{items.map((item) => <li key={item}>{item}</li>)}</ul></div> : null; }
function recommendationLabel(value: string) { return ({ strongly_recommended: "Strongly recommended for technical interview", recommended: "Recommended for technical interview", conditional: "Additional technical evidence recommended", insufficient_evidence: "Insufficient technical evidence", not_recommended: "Technical interview not recommended" } as Record<string, string>)[value] ?? "Evidence review"; }

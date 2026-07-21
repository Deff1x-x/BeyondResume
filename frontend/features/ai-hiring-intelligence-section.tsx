"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SkeletonCard } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/error";
import { useAiHiringIntelligenceQuery } from "@/lib/ai-hiring-intelligence/hooks";

export function AiHiringIntelligenceSection({ candidateId, vacancyId, enabled }: Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>) {
  const query = useAiHiringIntelligenceQuery(candidateId, vacancyId, enabled);
  if (query.isLoading) return <div role="status"><p className="text-sm text-secondary">Generating AI analysis...</p><SkeletonCard /></div>;
  if (query.isError || !query.data) return <div role="status" className="rounded-card border border-border bg-surface p-5"><p className="font-medium text-ink">AI analysis is temporarily unavailable.</p><p className="mt-2 text-sm leading-6 text-secondary">{unavailableMessage(query.error)}</p><Button size="sm" variant="secondary" className="mt-4" onClick={() => void query.refetch()}>Try again</Button></div>;
  const { verdict, interview_questions: questions } = query.data;
  return <div className="space-y-5"><Card><CardContent className="p-5"><p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">AI-generated analysis</p><h2 className="mt-2 text-lg font-semibold text-ink">Technical Interview Recommendation</h2><p className="mt-1 text-sm text-secondary">Evidence-based technical interview recommendation</p><p className="mt-3 text-sm font-medium text-primary">{recommendationLabel(verdict.technical_interview_recommendation)}</p><p className="mt-1 text-sm text-secondary">{verdict.confidence}% confidence</p><p className="mt-4 text-sm leading-6 text-secondary">{verdict.summary}</p><List title="Strengths" items={verdict.strengths} /><List title="Concerns" items={verdict.concerns} /></CardContent></Card><Card><CardContent className="p-5"><h2 className="text-lg font-semibold text-ink">Interview Questions</h2>{questions.length === 0 ? <p className="mt-3 text-sm text-secondary">No interview questions were generated for the available evidence.</p> : questions.map((item) => <div key={`${item.skill}-${item.question}`} className="mt-4 border-t border-border pt-4"><p className="text-sm font-medium text-ink">{item.skill} · {item.difficulty}</p><p className="mt-2 text-sm text-secondary">{item.question}</p><p className="mt-2 text-xs text-muted">Reason: {item.reason}</p></div>)}</CardContent></Card></div>;
}

function List({ title, items }: Readonly<{ title: string; items: string[] }>) { return items.length ? <div className="mt-4"><p className="text-sm font-medium text-ink">{title}</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-secondary">{items.map((item) => <li key={item}>{item}</li>)}</ul></div> : null; }

function recommendationLabel(value: string) { return ({ strongly_recommended: "Strongly recommended for technical interview", recommended: "Recommended for technical interview", conditional: "Additional technical evidence recommended", insufficient_evidence: "Insufficient technical evidence", not_recommended: "Technical interview not recommended" } as Record<string, string>)[value] ?? "Evidence review"; }

function unavailableMessage(error: unknown) { if (error instanceof ApiClientError && error.status === 503) return "The AI provider could not generate an analysis right now. Please try again later."; return "AI analysis could not be loaded right now. Please try again later."; }

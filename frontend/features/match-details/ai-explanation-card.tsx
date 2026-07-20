"use client";

import { Card, CardContent } from "@/components/ui/card";
import { SkeletonText } from "@/components/ui/skeleton";
import { useMatchExplanationQuery } from "@/lib/employer/hooks";

function ExplanationList({ title, items }: Readonly<{ title: string; items: string[] }>) {
  if (items.length === 0) return null;
  return <section><h3 className="text-sm font-semibold text-ink">{title}</h3><ul className="mt-2 space-y-2 text-sm leading-6 text-secondary">{items.map((item) => <li key={item} className="flex gap-2"><span aria-hidden="true">•</span><span>{item}</span></li>)}</ul></section>;
}

export function AiExplanationCard({ candidateId, vacancyId, enabled }: Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>) {
  const query = useMatchExplanationQuery(candidateId, vacancyId, enabled);
  return <Card aria-labelledby="ai-explanation-title"><CardContent className="p-5"><h2 id="ai-explanation-title" className="text-lg font-semibold tracking-tight text-ink">AI Explanation</h2>{query.isLoading ? <div className="mt-4" role="status"><p className="text-sm text-secondary">Generating explanation...</p><div className="mt-3 space-y-2"><SkeletonText /><SkeletonText className="w-4/5" /></div></div> : null}{query.isError ? <p className="mt-3 text-sm text-secondary" role="status">AI explanation is currently unavailable.</p> : null}{query.data ? <div className="mt-4 space-y-5"><p className="text-sm leading-6 text-secondary">{query.data.summary}</p><ExplanationList title="Strengths" items={query.data.strengths} /><ExplanationList title="Gaps" items={query.data.gaps} /><ExplanationList title="Next steps" items={query.data.next_steps} /></div> : null}</CardContent></Card>;
}

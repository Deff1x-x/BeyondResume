import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import type { MatchDetailsEvidence } from "@/lib/api/types/employer";

type EvidenceCardProps = Readonly<{ evidence: MatchDetailsEvidence[]; selectedSkill: string | null; onClearSkill: () => void }>;
function sourceLabel(sourceType: string): string { if (sourceType === "github_repository") return "GitHub"; if (sourceType === "resume") return "Résumé"; return sourceType.replaceAll("_", " "); }

export function EvidenceCard({ evidence, selectedSkill, onClearSkill }: EvidenceCardProps) {
  const visibleEvidence = selectedSkill ? evidence.filter((item) => item.skills.includes(selectedSkill)) : evidence;
  return <Card aria-labelledby="evidence-section-title"><CardContent className="p-5 sm:p-6"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">Evidence panel</p><h2 id="evidence-section-title" className="mt-2 text-xl font-semibold tracking-tight text-ink">Evidence behind the match</h2><p className="mt-2 text-sm leading-6 text-secondary">Select a skill to focus on the sources that support it.</p></div>{selectedSkill ? <Button size="sm" variant="secondary" onClick={onClearSkill}>Clear {selectedSkill}</Button> : null}</div>{visibleEvidence.length === 0 ? <EmptyState className="mt-5 bg-surface-subtle" title={selectedSkill ? `No evidence linked to ${selectedSkill}` : "No evidence linked yet"} description="This match has no safe evidence details available for the selected skill." /> : <ul className="mt-6 space-y-3">{visibleEvidence.map((item) => <li key={`${item.source_type}-${item.title ?? "untitled"}-${item.skills.join(",")}`} className="rounded-xl border border-border bg-surface/70 p-4"><div className="flex flex-wrap items-center gap-2"><Badge variant="neutral">{sourceLabel(item.source_type)}</Badge><p className="min-w-0 break-words text-sm font-medium text-ink">{item.title?.trim() || "Untitled evidence"}</p></div>{item.skills.length > 0 ? <ul className="mt-3 flex flex-wrap gap-2" aria-label="Evidence skills">{item.skills.map((skill) => <li key={skill}><Badge variant={selectedSkill === skill ? "primary" : "neutral"}>{skill}</Badge></li>)}</ul> : null}</li>)}</ul>}</CardContent></Card>;
}

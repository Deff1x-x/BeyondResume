import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import type { MatchDetailsEvidence } from "@/lib/api/types/employer";

type EvidenceCardProps = Readonly<{
  evidence: MatchDetailsEvidence[];
}>;

function sourceLabel(sourceType: string): string {
  if (sourceType === "github_repository") {
    return "GitHub";
  }
  if (sourceType === "resume") {
    return "Resume";
  }
  return sourceType.replaceAll("_", " ");
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <Card aria-labelledby="evidence-section-title">
      <CardContent className="space-y-5 p-5 sm:p-6">
        <SectionHeader
          title="Evidence"
          titleId="evidence-section-title"
          description="Sources that support the skills used in this match."
          size="md"
        />

        {evidence.length === 0 ? (
          <EmptyState
            title="No evidence linked yet"
            description="Evidence supporting this match will appear here when available."
            className="bg-surface-subtle"
          />
        ) : (
          <ul className="space-y-4">
            {evidence.map((item) => (
              <li
                key={`${item.source_type}-${item.title ?? "untitled"}-${item.skills.join(",")}`}
                className="border-t border-border pt-4 first:border-t-0 first:pt-0"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="neutral">{sourceLabel(item.source_type)}</Badge>
                  <p className="min-w-0 break-words text-sm font-medium text-ink">
                    {item.title?.trim() ? item.title : "Untitled evidence"}
                  </p>
                </div>
                {item.skills.length > 0 ? (
                  <ul className="mt-3 flex flex-wrap gap-2" aria-label="Evidence skills">
                    {item.skills.map((skill) => (
                      <li key={skill} className="min-w-0 max-w-full">
                        <Badge variant="neutral" title={skill}>
                          {skill}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-secondary">No skills linked.</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

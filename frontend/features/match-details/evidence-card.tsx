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
    <section
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby="evidence-section-title"
    >
      <h2 id="evidence-section-title" className="text-base font-semibold text-ink">
        Evidence
      </h2>
      <p className="mt-1 text-sm text-secondary">
        Sources that support the skills used in this match.
      </p>

      {evidence.length === 0 ? (
        <p className="mt-5 text-sm text-secondary">No evidence linked yet.</p>
      ) : (
        <ul className="mt-5 space-y-4">
          {evidence.map((item) => (
            <li
              key={`${item.source_type}-${item.title ?? "untitled"}-${item.skills.join(",")}`}
              className="border-t border-border pt-4 first:border-t-0 first:pt-0"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-button border border-border bg-background px-2.5 py-1 text-xs font-medium text-secondary">
                  {sourceLabel(item.source_type)}
                </span>
                <p className="text-sm font-medium text-ink">
                  {item.title?.trim() ? item.title : "Untitled evidence"}
                </p>
              </div>
              {item.skills.length > 0 ? (
                <ul className="mt-3 flex flex-wrap gap-2" aria-label="Evidence skills">
                  {item.skills.map((skill) => (
                    <li
                      key={skill}
                      className="rounded-button border border-border bg-background px-2.5 py-1 text-xs text-ink"
                    >
                      {skill}
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
    </section>
  );
}

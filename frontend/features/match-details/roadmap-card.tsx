import type { MatchDetailsRoadmapItem } from "@/lib/api/types/employer";

type RoadmapCardProps = Readonly<{
  items: MatchDetailsRoadmapItem[];
}>;

function priorityLabel(priority: MatchDetailsRoadmapItem["priority"]): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}

export function RoadmapCard({ items }: RoadmapCardProps) {
  return (
    <section
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby="roadmap-section-title"
    >
      <h2 id="roadmap-section-title" className="text-base font-semibold text-ink">
        Roadmap
      </h2>
      <p className="mt-1 text-sm text-secondary">
        Existing development suggestions from the candidate roadmap.
      </p>

      {items.length === 0 ? (
        <p className="mt-5 text-sm text-secondary">No roadmap items for this candidate.</p>
      ) : (
        <ol className="mt-5 space-y-4">
          {items.map((item) => (
            <li key={item.id} className="border-t border-border pt-4 first:border-t-0 first:pt-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-button border border-border bg-background px-2.5 py-1 text-xs font-medium text-secondary">
                  {priorityLabel(item.priority)}
                </span>
                <h3 className="text-sm font-medium text-ink">{item.title}</h3>
              </div>
              <p className="mt-2 text-sm leading-6 text-secondary">{item.reason}</p>
              {item.missing_skills.length > 0 ? (
                <p className="mt-2 text-sm text-secondary">
                  Missing:{" "}
                  <span className="text-ink">{item.missing_skills.join(", ")}</span>
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

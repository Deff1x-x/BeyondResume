import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import type { MatchDetailsRoadmapItem } from "@/lib/api/types/employer";

type RoadmapCardProps = Readonly<{
  items: MatchDetailsRoadmapItem[];
}>;

function priorityVariant(
  priority: MatchDetailsRoadmapItem["priority"]
): "neutral" | "warning" | "danger" | "accent" {
  if (priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  if (priority === "low") {
    return "accent";
  }
  return "neutral";
}

function priorityLabel(priority: MatchDetailsRoadmapItem["priority"]): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}

export function RoadmapCard({ items }: RoadmapCardProps) {
  return (
    <Card aria-labelledby="roadmap-section-title">
      <CardContent className="space-y-5 p-5 sm:p-6">
        <SectionHeader
          title="Roadmap"
          titleId="roadmap-section-title"
          description="Existing development suggestions from the candidate roadmap."
          size="md"
        />

        {items.length === 0 ? (
          <EmptyState
            title="No roadmap items"
            description="No roadmap items for this candidate."
            className="bg-surface-subtle"
          />
        ) : (
          <ol className="space-y-4">
            {items.map((item) => (
              <li key={item.id} className="border-t border-border pt-4 first:border-t-0 first:pt-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={priorityVariant(item.priority)}>
                    {priorityLabel(item.priority)}
                  </Badge>
                  <h3 className="min-w-0 break-words text-sm font-medium text-ink">
                    {item.title}
                  </h3>
                </div>
                <p className="mt-2 text-sm leading-6 text-secondary">{item.reason}</p>
                {item.missing_skills.length > 0 ? (
                  <p className="mt-2 text-sm text-secondary">
                    Missing:{" "}
                    <span className="break-words text-ink">
                      {item.missing_skills.join(", ")}
                    </span>
                  </p>
                ) : null}
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}

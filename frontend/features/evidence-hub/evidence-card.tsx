import type { EvidenceHubItem } from "@/lib/api/types/evidence";

import { EvidenceSkillBadges } from "./evidence-skill-badges";

function formatRelativeUpdated(value: string): string {
  const updated = new Date(value).getTime();
  const deltaMs = Date.now() - updated;
  const minutes = Math.max(0, Math.floor(deltaMs / 60_000));

  if (minutes < 1) {
    return "Updated just now";
  }
  if (minutes < 60) {
    return `Updated ${minutes}m ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 48) {
    return `Updated ${hours}h ago`;
  }

  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

function verificationLabel(status: string | null): string {
  if (!status) {
    return "Verification status unknown";
  }
  if (status === "unverified") {
    return "Unverified evidence";
  }
  return status.replaceAll("_", " ");
}

export function EvidenceCard({ item }: Readonly<{ item: EvidenceHubItem }>) {
  const title = item.title?.trim() || item.source.label;
  const badge = item.source.label;

  return (
    <article className="rounded-card border border-border bg-background px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-button border border-border bg-surface px-2 py-0.5 text-xs font-medium text-secondary">
              {badge}
            </span>
            <h3 className="break-words text-sm font-semibold text-ink">{title}</h3>
          </div>
          {item.description ? (
            <p className="mt-2 text-sm leading-6 text-secondary">{item.description}</p>
          ) : (
            <p className="mt-2 text-sm text-secondary">No description available.</p>
          )}
        </div>
        <p className="shrink-0 text-xs text-secondary">{formatRelativeUpdated(item.updated_at)}</p>
      </div>

      <div className="mt-3">
        <EvidenceSkillBadges skills={item.skills} />
      </div>

      <p className="mt-3 text-xs text-secondary" aria-label="Verification status">
        {verificationLabel(item.verification_status)}
      </p>
    </article>
  );
}

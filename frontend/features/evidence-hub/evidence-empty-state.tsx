import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

type EvidenceEmptyStateProps = {
  variant: "none" | "filtered" | "error";
  message?: string;
  onClearFilters?: () => void;
  onRetry?: () => void;
};

export function EvidenceEmptyState({
  variant,
  message,
  onClearFilters,
  onRetry
}: Readonly<EvidenceEmptyStateProps>) {
  if (variant === "error") {
    return (
      <EmptyState
        role="alert"
        title="Could not load evidence"
        description={message ?? "Something went wrong while loading your evidence."}
        primaryAction={
          onRetry ? (
            <Button type="button" variant="secondary" onClick={onRetry}>
              Retry
            </Button>
          ) : undefined
        }
      />
    );
  }

  if (variant === "filtered") {
    return (
      <EmptyState
        title="No evidence matches these filters"
        description="Try a different search term or clear the active filters."
        primaryAction={
          onClearFilters ? (
            <Button type="button" variant="secondary" onClick={onClearFilters}>
              Clear filters
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <EmptyState
      title="No evidence yet"
      description="Connect GitHub or upload a resume to start collecting evidence."
      primaryAction={
        <a
          href="#github-section-title"
          className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        >
          Connect GitHub
        </a>
      }
      secondaryAction={
        <a
          href="#resume-section-title"
          className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        >
          Upload resume
        </a>
      }
    />
  );
}

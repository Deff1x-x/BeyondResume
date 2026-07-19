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
      <div
        className="rounded-card border border-border bg-background px-4 py-8 text-center"
        role="alert"
      >
        <p className="text-sm font-medium text-ink">Could not load evidence</p>
        <p className="mt-2 text-sm text-secondary">
          {message ?? "Something went wrong while loading your evidence."}
        </p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          >
            Retry
          </button>
        ) : null}
      </div>
    );
  }

  if (variant === "filtered") {
    return (
      <div className="rounded-card border border-border bg-background px-4 py-8 text-center">
        <p className="text-sm font-medium text-ink">No evidence matches these filters</p>
        <p className="mt-2 text-sm text-secondary">
          Try a different search term or clear the active filters.
        </p>
        {onClearFilters ? (
          <button
            type="button"
            onClick={onClearFilters}
            className="mt-4 inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          >
            Clear filters
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-card border border-border bg-background px-4 py-8 text-center">
      <p className="text-sm font-medium text-ink">No evidence yet</p>
      <p className="mt-2 text-sm text-secondary">
        Connect GitHub or upload a resume to start collecting evidence.
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-3">
        <a
          href="#github-section-title"
          className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Connect GitHub
        </a>
        <a
          href="#resume-section-title"
          className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Upload resume
        </a>
      </div>
    </div>
  );
}

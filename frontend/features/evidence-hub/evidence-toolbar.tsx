type SourceFilter = "all" | "github" | "resume";

type EvidenceToolbarProps = {
  search: string;
  sourceFilter: SourceFilter;
  skill: string;
  onSearchChange: (value: string) => void;
  onSourceFilterChange: (value: SourceFilter) => void;
  onSkillChange: (value: string) => void;
};

const SOURCE_OPTIONS: { value: SourceFilter; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "github", label: "GitHub" },
  { value: "resume", label: "Resume" }
];

export function EvidenceToolbar({
  search,
  sourceFilter,
  skill,
  onSearchChange,
  onSourceFilterChange,
  onSkillChange
}: Readonly<EvidenceToolbarProps>) {
  return (
    <div className="flex flex-col gap-3 border-b border-border pb-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="min-w-0 flex-1 text-sm text-secondary">
          Search evidence
          <input
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search by title or description"
            className="mt-1.5 min-h-control w-full rounded-button border border-border bg-background px-3 text-sm text-ink outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
          />
        </label>
        <label className="w-full text-sm text-secondary sm:w-48">
          Skill
          <input
            type="text"
            value={skill}
            onChange={(event) => onSkillChange(event.target.value)}
            placeholder="e.g. Python"
            className="mt-1.5 min-h-control w-full rounded-button border border-border bg-background px-3 text-sm text-ink outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
          />
        </label>
      </div>

      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Filter by source"
      >
        {SOURCE_OPTIONS.map((option) => {
          const selected = sourceFilter === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onSourceFilterChange(option.value)}
              className={
                selected
                  ? "min-h-control rounded-button border border-ink bg-ink px-3 text-sm font-medium text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                  : "min-h-control rounded-button border border-border bg-surface px-3 text-sm font-medium text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              }
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export type { SourceFilter };

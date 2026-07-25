import { cn } from "@/lib/cn";
import { Icon } from "@/components/ui/icon";

const STEPS = [
  { id: "select", label: "Select candidates" },
  { id: "compare", label: "Compare" },
  { id: "ai", label: "AI Hiring Analysis" }
] as const;

export type CompareFlowStepId = (typeof STEPS)[number]["id"];

export type CompareFlowStepsProps = Readonly<{
  active: CompareFlowStepId;
  className?: string;
}>;

export function CompareFlowSteps({ active, className }: CompareFlowStepsProps) {
  const activeIndex = STEPS.findIndex((step) => step.id === active);

  return (
    <nav
      aria-label="Candidate comparison flow"
      className={cn(
        "rounded-card border border-border bg-surface px-5 py-4 shadow-card sm:px-6",
        className
      )}
    >
      <ol className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
        {STEPS.map((step, index) => {
          const isActive = index === activeIndex;
          const isComplete = index < activeIndex;
          return (
            <li key={step.id} className="flex items-center gap-3">
              {index > 0 ? (
                <span
                  aria-hidden="true"
                  className="hidden text-muted sm:inline"
                >
                  <Icon name="arrow-right" className="h-3.5 w-3.5" />
                </span>
              ) : null}
              <span
                className={cn(
                  "inline-flex items-center gap-2.5 rounded-card px-3 py-2 text-sm transition duration-200",
                  isActive && "bg-ai/10 font-semibold text-ai-muted ring-1 ring-ai/25",
                  isComplete && "font-medium text-ink",
                  !isActive && !isComplete && "text-secondary"
                )}
                aria-current={isActive ? "step" : undefined}
              >
                <span
                  className={cn(
                    "inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                    isActive && "bg-accent text-accent-foreground",
                    isComplete && "bg-primary/10 text-primary",
                    !isActive && !isComplete && "bg-surface-subtle text-secondary ring-1 ring-border"
                  )}
                >
                  {isComplete ? <Icon name="check" className="h-3.5 w-3.5" /> : index + 1}
                </span>
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function CompareValueProps({ className }: Readonly<{ className?: string }>) {
  const items = [
    "Side-by-side deterministic comparison",
    "AI Hiring Analysis as a second opinion",
    "Hiring risks, onboarding insights, interview focus"
  ];

  return (
    <ul
      className={cn("grid gap-3 sm:grid-cols-3 sm:gap-4", className)}
      aria-label="What you get from comparison"
    >
      {items.map((item) => (
        <li
          key={item}
          className="flex min-h-[4.75rem] items-start gap-3 rounded-card border border-border bg-surface-subtle/70 px-4 py-3.5 text-sm leading-6 text-ink"
        >
          <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success/15 text-success">
            <Icon name="check" className="h-3 w-3" />
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

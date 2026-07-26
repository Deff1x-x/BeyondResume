"use client";

import { useCallback, type ReactNode } from "react";

import { ActionToast, useActionToast } from "@/components/ui/action-toast";
import { Icon } from "@/components/ui/icon";
import { ApiClientError } from "@/lib/api/error";
import { cn } from "@/lib/cn";
import {
  useApplyToVacancy,
  useWithdrawApplication
} from "@/lib/candidate-vacancies/hooks";

function applicationErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "Application could not be updated. Please try again.";
}

/** Shared metrics so every CTA state keeps identical geometry. */
const ctaMetricsClass = cn(
  "inline-flex h-12 w-full items-center justify-center gap-2 rounded-button px-4",
  "text-sm font-semibold tracking-tight"
);

const ctaMotionClass = cn(
  "transition-[color,background-color,border-color,box-shadow,transform,opacity] duration-200 ease-out",
  "motion-reduce:transition-none motion-reduce:hover:translate-y-0 motion-reduce:active:scale-100"
);

const ctaFocusClass = cn(
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed"
);

const iconClass = "h-4 w-4 shrink-0";

/**
 * Primary Apply — lime gradient, soft accent shadow (aligned with Button primary).
 * Kept calmer than Match Score’s circular badge by avoiding heavy glow / large lift.
 */
const applyPrimaryClass = cn(
  ctaMetricsClass,
  ctaMotionClass,
  ctaFocusClass,
  "relative border border-accent bg-gradient-to-b from-accent to-accent-hover text-accent-foreground",
  "shadow-sm shadow-accent/25",
  "hover:-translate-y-px hover:from-accent-hover hover:to-accent-muted hover:shadow-md hover:shadow-accent/30",
  "active:translate-y-0 active:scale-[0.98] active:shadow-sm",
  "disabled:border-border disabled:bg-none disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none disabled:hover:translate-y-0"
);

/** Outline lime — same 1px border width as primary to avoid box-model jitter. */
const applyAgainClass = cn(
  ctaMetricsClass,
  ctaMotionClass,
  ctaFocusClass,
  "relative border border-accent bg-surface text-accent-muted shadow-sm",
  "hover:-translate-y-px hover:bg-accent-soft hover:shadow-md hover:shadow-accent/15",
  "active:translate-y-0 active:scale-[0.98] active:shadow-sm",
  "disabled:border-border disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none disabled:hover:translate-y-0"
);

/** Status chip — not a CTA: no shadow, no lift, medium weight. */
const appliedStatusClass = cn(
  ctaMetricsClass,
  "border border-success/30 bg-success-soft font-medium text-success-muted shadow-none"
);

/** Secondary / soft-destructive — quieter than Apply, never filled. */
const withdrawClass = cn(
  ctaMetricsClass,
  ctaMotionClass,
  ctaFocusClass,
  "relative border border-danger/30 bg-surface text-danger-muted shadow-sm",
  "hover:border-danger/45 hover:bg-danger-soft hover:shadow-sm",
  "active:scale-[0.98]",
  "disabled:border-border disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none"
);

function Spinner({ className }: Readonly<{ className?: string }>) {
  return (
    <span
      className={cn(
        "h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none",
        className
      )}
      aria-hidden="true"
    />
  );
}

function ButtonLabel({
  loading,
  loadingLabel,
  children
}: Readonly<{
  loading: boolean;
  loadingLabel: string;
  children: ReactNode;
}>) {
  return (
    <>
      <span className={cn("inline-flex items-center gap-2", loading && "invisible")}>
        {children}
      </span>
      {loading ? (
        <span
          className="absolute inset-0 flex items-center justify-center gap-2"
          aria-hidden="true"
        >
          <Spinner />
          <span>{loadingLabel}</span>
        </span>
      ) : null}
    </>
  );
}

type VacancyApplicationActionsProps = Readonly<{
  vacancyId: string;
  applicationStatus: string | null | undefined;
  vacancyTitle?: string;
}>;

export function VacancyApplicationActions({
  vacancyId,
  applicationStatus,
  vacancyTitle
}: VacancyApplicationActionsProps) {
  const applyMutation = useApplyToVacancy(vacancyId);
  const withdrawMutation = useWithdrawApplication(vacancyId);
  const { toast, showToast, dismissToast } = useActionToast();
  const onDismiss = useCallback(() => dismissToast(), [dismissToast]);

  const isApplied = applicationStatus === "applied";
  const isWithdrawn = applicationStatus === "withdrawn";
  const pending = applyMutation.isPending || withdrawMutation.isPending;
  const error = applyMutation.error ?? withdrawMutation.error;
  const labelContext = vacancyTitle ? ` for ${vacancyTitle}` : "";

  function onApply() {
    applyMutation.mutate(undefined, {
      onSuccess: () => {
        showToast("You successfully applied to this vacancy.", "success");
      }
    });
  }

  function onWithdraw() {
    withdrawMutation.mutate(undefined, {
      onSuccess: () => {
        showToast("Application withdrawn.", "neutral");
      }
    });
  }

  return (
    <div className="flex w-full flex-col gap-2">
      {/* Fixed single-row height (h-12) across Apply / Applied+Withdraw / Apply again */}
      {isApplied ? (
        <div className="grid w-full grid-cols-2 gap-2">
          <div
            className={appliedStatusClass}
            role="status"
            aria-label={`Applied${labelContext}`}
          >
            <Icon name="check-circle" className={iconClass} />
            <span>Applied</span>
          </div>
          <button
            type="button"
            className={withdrawClass}
            disabled={pending}
            aria-busy={withdrawMutation.isPending || undefined}
            aria-label={`Withdraw application${labelContext}`}
            onClick={onWithdraw}
          >
            <ButtonLabel
              loading={withdrawMutation.isPending}
              loadingLabel="Withdrawing..."
            >
              <Icon name="undo" className={iconClass} />
              <span>Withdraw</span>
            </ButtonLabel>
          </button>
        </div>
      ) : (
        <button
          type="button"
          className={isWithdrawn ? applyAgainClass : applyPrimaryClass}
          disabled={pending}
          aria-busy={applyMutation.isPending || undefined}
          aria-label={
            applyMutation.isPending
              ? `Applying${labelContext}`
              : isWithdrawn
                ? `Apply again${labelContext}`
                : `Apply now${labelContext}`
          }
          onClick={onApply}
        >
          <ButtonLabel loading={applyMutation.isPending} loadingLabel="Applying...">
            <Icon name="send" className={iconClass} />
            <span>Apply now</span>
          </ButtonLabel>
        </button>
      )}

      {error ? (
        <p className="text-sm text-danger" role="alert">
          {applicationErrorMessage(error)}
        </p>
      ) : null}

      <ActionToast toast={toast} onDismiss={onDismiss} />
    </div>
  );
}

/** Secondary card action — shorter than Apply so hierarchy stays clear. */
export const vacancyViewDetailsClass = cn(
  "inline-flex h-11 w-full items-center justify-center gap-2 rounded-button border border-border-strong bg-surface px-4 text-sm font-semibold tracking-tight text-ink shadow-sm",
  "transition-[color,background-color,border-color,box-shadow,transform] duration-200 ease-out",
  "hover:-translate-y-px hover:border-ink/20 hover:bg-background hover:shadow-md",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
  "active:translate-y-0 active:scale-[0.98] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
);

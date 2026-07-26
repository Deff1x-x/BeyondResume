import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "ink" | "secondary" | "ghost" | "destructive";
type ButtonSize = "sm" | "md";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: ReactNode;
};

/**
 * Product CTA language matches Landing:
 * Lime fill + Navy label + soft lift on hover.
 * `ink` is reserved for rare high-contrast dark actions.
 */
export const buttonVariantClass: Record<ButtonVariant, string> = {
  primary:
    "border border-accent bg-accent text-accent-foreground shadow-sm shadow-accent/25 hover:-translate-y-px hover:bg-accent-hover hover:shadow-md active:translate-y-0 active:shadow-sm disabled:border-border disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none disabled:hover:translate-y-0",
  ink:
    "border border-primary bg-primary text-primary-foreground shadow-sm hover:-translate-y-px hover:bg-primary-hover hover:shadow-md active:translate-y-0 active:shadow-sm disabled:border-border disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none disabled:hover:translate-y-0",
  secondary:
    "border border-border-strong bg-surface text-ink shadow-sm hover:-translate-y-px hover:border-ink/20 hover:bg-background hover:shadow-md active:translate-y-0 active:shadow-sm disabled:border-border disabled:bg-surface-subtle disabled:text-secondary",
  ghost:
    "border border-transparent bg-transparent text-secondary hover:bg-surface-subtle hover:text-ink disabled:text-muted",
  destructive:
    "border border-danger bg-danger text-danger-foreground shadow-sm hover:-translate-y-px hover:bg-danger/90 hover:shadow-md active:translate-y-0 active:shadow-sm disabled:border-border disabled:bg-surface-subtle disabled:text-secondary disabled:shadow-none"
};

export const buttonSizeClass: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 text-sm",
  md: "min-h-control px-4 text-sm"
};

export const buttonBaseClass = cn(
  "relative inline-flex items-center justify-center gap-2 rounded-button font-semibold tracking-tight transition-all duration-200 ease-out",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed motion-reduce:transition-none motion-reduce:hover:translate-y-0"
);

/** Link / anchor that should look like a primary Landing CTA. */
export const primaryActionClass = cn(
  buttonBaseClass,
  buttonVariantClass.primary,
  buttonSizeClass.md
);

export const secondaryActionClass = cn(
  buttonBaseClass,
  buttonVariantClass.secondary,
  buttonSizeClass.md
);

/** @deprecated Prefer `primary` — kept as alias for gradual call-site cleanup. */
export const accentActionClass = primaryActionClass;

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "secondary",
    size = "md",
    loading = false,
    disabled,
    className,
    children,
    type = "button",
    ...props
  },
  ref
) {
  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={cn(
        buttonBaseClass,
        buttonVariantClass[variant],
        buttonSizeClass[size],
        className
      )}
      {...props}
    >
      <span className={cn("inline-flex items-center gap-2", loading && "invisible")}>
        {children}
      </span>
      {loading ? (
        <span
          className="absolute inset-0 flex items-center justify-center"
          aria-hidden="true"
        >
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none" />
        </span>
      ) : null}
    </button>
  );
});

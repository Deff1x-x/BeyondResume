import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
type ButtonSize = "sm" | "md";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: ReactNode;
};

const variantClass: Record<ButtonVariant, string> = {
  primary:
    "border border-primary bg-primary text-white hover:bg-primary/90 disabled:border-primary/50 disabled:bg-primary/50",
  secondary:
    "border border-border bg-surface text-ink hover:bg-surface-subtle disabled:text-muted",
  ghost:
    "border border-transparent bg-transparent text-ink hover:bg-surface-subtle disabled:text-muted",
  destructive:
    "border border-danger bg-danger text-white hover:bg-danger/90 disabled:border-danger/50 disabled:bg-danger/50"
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 text-sm",
  md: "min-h-control px-4 text-sm"
};

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
        "relative inline-flex items-center justify-center gap-2 rounded-button font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-60",
        variantClass[variant],
        sizeClass[size],
        className
      )}
      {...props}
    >
      <span className={cn(loading && "invisible")}>{children}</span>
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

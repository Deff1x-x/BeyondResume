import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

/** Shared surface for text inputs, selects, and textareas. */
export const controlClassName = cn(
  "w-full rounded-input border border-border bg-surface/90 text-sm text-ink shadow-sm outline-none transition-all duration-200",
  "placeholder:text-muted",
  "hover:border-border-strong focus-visible:border-primary focus-visible:ring-4 focus-visible:ring-focus-ring/15 focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed disabled:bg-background disabled:text-muted"
);

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, type = "text", ...props },
  ref
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(controlClassName, "min-h-control px-3", className)}
      {...props}
    />
  );
});

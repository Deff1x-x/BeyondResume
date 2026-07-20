import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

/** Shared surface for text inputs, selects, and textareas. */
export const controlClassName = cn(
  "w-full rounded-input border border-border bg-surface text-sm text-ink outline-none transition-colors",
  "placeholder:text-muted",
  "focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
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

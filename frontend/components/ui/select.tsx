import { forwardRef, type SelectHTMLAttributes } from "react";

import { controlClassName } from "@/components/ui/input";
import { cn } from "@/lib/cn";

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, children, ...props },
  ref
) {
  return (
    <select
      ref={ref}
      className={cn(controlClassName, "min-h-control px-3", className)}
      {...props}
    >
      {children}
    </select>
  );
});

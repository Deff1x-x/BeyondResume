import { forwardRef, type TextareaHTMLAttributes } from "react";

import { controlClassName } from "@/components/ui/input";
import { cn } from "@/lib/cn";

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { className, rows = 3, ...props },
  ref
) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(controlClassName, "min-h-[5.5rem] px-3 py-2", className)}
      {...props}
    />
  );
});

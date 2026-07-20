import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

export type PageContainerProps = HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  as?: "main" | "div";
  /** Center content vertically (auth pages). */
  centered?: boolean;
  /** Narrow column for auth forms. */
  narrow?: boolean;
};

export function PageContainer({
  children,
  as: Tag = "main",
  centered = false,
  narrow = false,
  className,
  ...props
}: PageContainerProps) {
  return (
    <Tag
      className={cn(
        narrow ? "mx-auto w-full max-w-md px-6 py-12 sm:py-16" : "mx-auto w-full max-w-7xl px-5 py-10 sm:px-6 lg:px-8 lg:py-14",
        centered && "flex min-h-screen flex-col justify-center",
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

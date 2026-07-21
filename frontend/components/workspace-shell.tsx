import type { ReactNode } from "react";

import { WorkspaceNavigation } from "@/components/workspace-navigation";

export function WorkspaceShell({
  role,
  email,
  children
}: Readonly<{ role: "candidate" | "employer"; email?: string; children: ReactNode }>) {
  return (
    <div className="min-h-screen lg:flex">
      <WorkspaceNavigation role={role} email={email} />
      <main id="workspace-content" className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-7xl px-5 py-8 sm:px-8 sm:py-10 xl:px-12 xl:py-12">
          {children}
        </div>
      </main>
    </div>
  );
}

import Link from "next/link";
import type { ReactNode } from "react";

import { EvidenceFlowVisual } from "@/components/evidence-flow-visual";
import { BrandMark } from "@/components/ui/icon";

export function AuthShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <main className="min-h-screen overflow-x-hidden bg-background lg:grid lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)]">
      <aside className="relative hidden overflow-hidden bg-primary px-10 py-10 text-white lg:flex lg:flex-col xl:px-14">
        <Link
          href="/"
          className="relative flex w-fit items-center gap-3 rounded-control focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
        >
          <BrandMark />
          <span className="font-display text-sm font-semibold tracking-tight">BeyondResume</span>
        </Link>

        <div className="relative my-auto max-w-xl py-12">
          <p className="text-xs font-semibold tracking-wide text-accent">Evidence Intelligence</p>
          <h1 className="mt-4 font-display text-3xl font-semibold tracking-[-0.03em] xl:text-4xl">
            Skills become evidence.
            <span className="mt-2 block">Evidence becomes clarity.</span>
          </h1>
          <p className="mt-5 max-w-md text-base leading-7 text-primary-200">
            One product path for candidates and employers — verified signals first, AI only as a
            grounded second layer.
          </p>

          <div className="mt-10 rounded-card border border-white/12 bg-white/5 p-4">
            <EvidenceFlowVisual compact inverted />
          </div>
        </div>

        <p className="relative text-sm text-primary-300">
          Evidence over claims · Transparent matching · AI grounded in facts
        </p>
      </aside>

      <section className="relative flex min-h-screen items-start justify-center bg-background px-5 py-8 sm:px-8 sm:py-12 lg:items-center lg:px-12">
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}

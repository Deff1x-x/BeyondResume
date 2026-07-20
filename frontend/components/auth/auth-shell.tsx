import Link from "next/link";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/ui/icon";

export function AuthShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <main className="auth-shell min-h-screen lg:grid lg:grid-cols-[minmax(0,1.05fr)_minmax(440px,.95fr)]">
      <aside className="relative hidden overflow-hidden bg-slate-950 px-10 py-10 text-white lg:flex lg:flex-col xl:px-16">
        <div className="auth-glow auth-glow-one" aria-hidden="true" />
        <div className="auth-glow auth-glow-two" aria-hidden="true" />
        <Link href="/" className="relative flex w-fit items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950">
          <BrandMark /><span className="text-sm font-semibold tracking-wide">BeyondResume</span>
        </Link>
        <div className="relative my-auto max-w-xl py-16">
          <p className="text-sm font-semibold uppercase tracking-[.14em] text-cyan-300">Proof over assumptions</p>
          <h1 className="mt-5 text-4xl font-semibold tracking-[-.045em] xl:text-5xl">A clearer way to show what you can do.</h1>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">Bring skills, evidence, and potential into one professional story that is easier to trust.</p>
          <div className="mt-10 grid max-w-lg gap-3 sm:grid-cols-3">
            {["Evidence-backed", "Skills visible", "Matching made clear"].map((item) => <div key={item} className="rounded-xl border border-white/10 bg-white/5 px-3 py-3 text-xs font-medium text-slate-200">{item}</div>)}
          </div>
          <div className="relative mt-12 max-w-md">
            <div className="rounded-2xl border border-white/15 bg-white/10 p-5 shadow-2xl backdrop-blur-sm">
              <div className="flex items-center justify-between"><div className="flex items-center gap-3"><span className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-400 to-cyan-300" /><div><p className="text-sm font-semibold">Evidence profile</p><p className="text-xs text-slate-300">Frontend engineer</p></div></div><span className="rounded-full bg-emerald-400/15 px-2.5 py-1 text-xs font-semibold text-emerald-300">Verified</span></div>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full w-[82%] rounded-full bg-cyan-300" /></div>
              <div className="mt-4 flex flex-wrap gap-2"><span className="rounded-md bg-white/10 px-2 py-1 text-xs">React</span><span className="rounded-md bg-white/10 px-2 py-1 text-xs">TypeScript</span><span className="rounded-md bg-white/10 px-2 py-1 text-xs">GitHub evidence</span></div>
            </div>
            <div className="absolute -bottom-6 -right-8 rounded-xl border border-white/15 bg-slate-900/95 px-4 py-3 shadow-xl"><p className="text-xs text-slate-400">Role match</p><p className="mt-1 text-xl font-semibold text-cyan-300">92%</p></div>
          </div>
        </div>
        <p className="relative text-sm text-slate-400">Evidence-based profiles. Transparent matching. No résumé guesswork.</p>
      </aside>
      <section className="relative flex min-h-screen items-start justify-center px-5 py-8 sm:px-8 sm:py-12 lg:items-center lg:px-12">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_80%_8%,rgba(99,102,241,.13),transparent_22rem)]" aria-hidden="true" />
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}

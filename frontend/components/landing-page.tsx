import Link from "next/link";
import type { ReactNode } from "react";

import { EvidenceFlowVisual } from "@/components/evidence-flow-visual";
import { Reveal } from "@/components/reveal";
import { BrandMark } from "@/components/ui/icon";
import { cn } from "@/lib/cn";

const trustValues = [
  {
    title: "Evidence over claims",
    body: "Skills link to concrete proof from resume, GitHub, and work samples."
  },
  {
    title: "Transparent matching",
    body: "Employers compare candidates on verified signals, not keyword theatre."
  },
  {
    title: "AI grounded in facts",
    body: "AI interprets evidence to focus interviews — it never replaces the decision."
  }
] as const;

const howItWorks = [
  {
    title: "Connect signals",
    body: "Bring resume and GitHub evidence into one structured profile."
  },
  {
    title: "Verify skills",
    body: "Evidence units map to a living Skill Passport employers can trust."
  },
  {
    title: "Match with clarity",
    body: "Scores stay explainable — every gap and strength has a source."
  },
  {
    title: "Decide with context",
    body: "AI hiring insights highlight what to probe, grounded in the same facts."
  }
] as const;

function LandingNav() {
  return (
    <header className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
      <Link
        href="/"
        className="flex items-center gap-3 rounded-control focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
      >
        <BrandMark />
        <span className="font-display text-base font-semibold tracking-tight text-ink">
          BeyondResume
        </span>
      </Link>

      <nav
        className="hidden items-center gap-7 text-sm text-secondary md:flex"
        aria-label="Product"
      >
        <a href="#product" className="transition-colors duration-fast hover:text-ink">
          Product
        </a>
        <a href="#for-candidates" className="transition-colors duration-fast hover:text-ink">
          For candidates
        </a>
        <a href="#for-employers" className="transition-colors duration-fast hover:text-ink">
          For employers
        </a>
      </nav>

      <div className="flex items-center gap-2 sm:gap-3">
        <Link
          href="/login"
          className="hidden text-sm font-semibold text-ink transition-colors duration-fast hover:text-accent-muted sm:inline"
        >
          Sign in
        </Link>
        <Link
          href="/register"
          className="inline-flex min-h-10 items-center justify-center rounded-button border border-accent bg-accent px-3.5 text-sm font-semibold text-accent-foreground shadow-sm transition duration-fast hover:-translate-y-px hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 sm:min-h-control sm:px-4"
        >
          Get started
        </Link>
      </div>
    </header>
  );
}

function ProductMockCard({
  title,
  children,
  className
}: Readonly<{ title: string; children: ReactNode; className?: string }>) {
  return (
    <article
      className={cn(
        "rounded-card border border-border bg-surface p-5 shadow-card",
        className
      )}
    >
      <p className="text-xs font-medium text-secondary">{title}</p>
      <div className="mt-3">{children}</div>
    </article>
  );
}

export function LandingPage({ sessionError }: Readonly<{ sessionError: boolean }>) {
  return (
    <main className="overflow-x-hidden bg-background">
      <LandingNav />

      {/* Hero */}
      <section
        id="product"
        className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-8 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pb-28 lg:pt-14"
      >
        <Reveal>
          <p className="inline-flex items-center gap-2 rounded-badge border border-border bg-surface px-3 py-1.5 text-xs font-medium text-secondary">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
            Evidence Intelligence
          </p>
          <h1 className="mt-6 max-w-2xl font-display text-4xl font-semibold tracking-[-0.04em] text-ink sm:text-5xl lg:text-6xl">
            Turn your skills into evidence.
            <span className="mt-2 block text-ink">Turn evidence into opportunity.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-secondary sm:text-lg sm:leading-8">
            Candidates build an evidence-backed professional profile. Employers compare people
            with verified skills and AI insights grounded in those same facts — never vibes alone.
          </p>
          {sessionError ? (
            <p className="mt-4 text-sm text-danger" role="alert">
              We could not verify your session. Sign in to continue.
            </p>
          ) : null}
          <div className="mt-9 flex flex-wrap gap-3">
            <Link
              href="/register"
              className="inline-flex min-h-control items-center justify-center rounded-button border border-accent bg-accent px-6 text-sm font-semibold text-accent-foreground shadow-sm shadow-accent/25 transition duration-fast hover:-translate-y-px hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Build your evidence profile
            </Link>
            <a
              href="#for-employers"
              className="inline-flex min-h-control items-center justify-center rounded-button border border-border-strong bg-surface px-6 text-sm font-semibold text-ink transition duration-fast hover:-translate-y-px hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
            >
              Explore employer workflow
            </a>
          </div>
        </Reveal>

        <Reveal delay={100} className="mx-auto w-full max-w-xl">
          <div className="rounded-card border border-border bg-surface p-5 shadow-float sm:p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="font-display text-sm font-semibold text-ink">Evidence flow</p>
                <p className="text-xs text-secondary">How proof becomes a hiring decision</p>
              </div>
              <span className="rounded-badge border border-ai/30 bg-ai/10 px-2.5 py-1 text-[11px] font-semibold text-ai-muted">
                Live product path
              </span>
            </div>
            <EvidenceFlowVisual />
          </div>
        </Reveal>
      </section>

      {/* Trust strip */}
      <section
        aria-label="Product values"
        className="border-y border-border bg-surface"
      >
        <div className="mx-auto grid max-w-7xl gap-px bg-border sm:grid-cols-3">
          {trustValues.map((item, index) => (
            <Reveal key={item.title} delay={index * 80}>
              <div className="h-full bg-surface px-6 py-8 sm:px-8">
                <h2 className="font-display text-base font-semibold text-ink">{item.title}</h2>
                <p className="mt-2 max-w-sm text-sm leading-6 text-secondary">{item.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Candidate story */}
      <section id="for-candidates" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-24">
        <Reveal>
          <p className="text-xs font-semibold tracking-wide text-accent-muted">For candidates</p>
          <h2 className="mt-3 max-w-2xl font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            GitHub + Resume → Skill Passport → Opportunities
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-secondary">
            Connect your signals once. BeyondResume turns them into verified skills and a profile
            employers can actually evaluate.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-4 lg:grid-cols-3">
          <Reveal delay={0}>
            <ProductMockCard title="1 · Sources">
              <ul className="space-y-2 text-sm text-ink">
                <li className="flex items-center justify-between rounded-control border border-border bg-background px-3 py-2">
                  Resume uploaded
                  <span className="text-xs font-medium text-success-muted">Parsed</span>
                </li>
                <li className="flex items-center justify-between rounded-control border border-border bg-background px-3 py-2">
                  GitHub connected
                  <span className="text-xs font-medium text-success-muted">Linked</span>
                </li>
              </ul>
            </ProductMockCard>
          </Reveal>
          <Reveal delay={80}>
            <ProductMockCard title="2 · Skill Passport">
              <div className="flex flex-wrap gap-2">
                {["TypeScript", "React", "API design"].map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1.5 rounded-badge border border-verified/35 bg-verified/15 px-2.5 py-1 text-xs font-semibold text-verified-muted"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                    {skill}
                  </span>
                ))}
              </div>
              <p className="mt-4 text-xs leading-5 text-secondary">
                Each skill points back to evidence units — not self-rated stars.
              </p>
            </ProductMockCard>
          </Reveal>
          <Reveal delay={160}>
            <ProductMockCard title="3 · Opportunities">
              <div className="rounded-control border border-border bg-background p-3">
                <p className="text-sm font-semibold text-ink">Senior Frontend Engineer</p>
                <div className="mt-3 flex items-end justify-between">
                  <span className="text-xs text-secondary">Match</span>
                  <span className="font-display text-2xl font-semibold tabular-nums text-ink">
                    88%
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-subtle">
                  <div className="h-full w-[88%] rounded-full bg-accent" />
                </div>
              </div>
            </ProductMockCard>
          </Reveal>
        </div>
      </section>

      {/* Employer story */}
      <section id="for-employers" className="bg-primary py-20 text-white lg:py-24">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <Reveal>
            <p className="text-xs font-semibold tracking-wide text-accent">For employers</p>
            <h2 className="mt-3 max-w-2xl font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Shortlist → Compare → AI Hiring Analysis → Interview focus
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-7 text-primary-200">
              Run the real BeyondResume hiring path: deterministic evidence first, then AI as a
              second opinion that stays tied to the facts you already reviewed.
            </p>
          </Reveal>

          <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Shortlist", "Save strong matches with notes and stage."],
              ["Compare", "Side-by-side skills, evidence, and scores."],
              ["AI Hiring Analysis", "Grounded insights — never a black-box rank."],
              ["Interview focus", "Questions and scorecards aimed at real gaps."]
            ].map(([title, body], index) => (
              <Reveal key={title} delay={index * 70}>
                <article className="h-full rounded-card border border-white/12 bg-white/5 p-5">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-control bg-accent text-xs font-bold text-accent-foreground">
                    {index + 1}
                  </span>
                  <h3 className="mt-4 font-display text-base font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-primary-200">{body}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-24">
        <Reveal>
          <p className="text-xs font-semibold tracking-wide text-ai-muted">How it works</p>
          <h2 className="mt-3 max-w-xl font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            From scattered signals to a clear decision.
          </h2>
        </Reveal>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {howItWorks.map((step, index) => (
            <Reveal key={step.title} delay={index * 70}>
              <article className="h-full border-l-2 border-accent pl-4">
                <span className="text-xs font-semibold tabular-nums text-muted">
                  0{index + 1}
                </span>
                <h3 className="mt-3 font-display text-lg font-semibold text-ink">{step.title}</h3>
                <p className="mt-2 text-sm leading-6 text-secondary">{step.body}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="border-t border-border bg-surface">
        <div className="mx-auto max-w-5xl px-5 py-20 text-center sm:px-8">
          <Reveal>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
              Choose your path
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-base leading-7 text-secondary">
              Same product. Two clear entry points — evidence profile or hiring intelligence.
            </p>
            <div className="mx-auto mt-10 grid max-w-2xl gap-4 sm:grid-cols-2">
              <Link
                href="/register"
                className="rounded-card border border-border bg-background p-6 text-left transition duration-normal hover:-translate-y-px hover:border-accent/50 hover:shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
              >
                <p className="font-display text-lg font-semibold text-ink">I am a candidate</p>
                <p className="mt-2 text-sm leading-6 text-secondary">
                  Build an evidence-backed professional profile.
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-accent-muted">
                  Create candidate account →
                </span>
              </Link>
              <Link
                href="/register"
                className="rounded-card border border-border bg-background p-6 text-left transition duration-normal hover:-translate-y-px hover:border-ai/50 hover:shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
              >
                <p className="font-display text-lg font-semibold text-ink">I am hiring</p>
                <p className="mt-2 text-sm leading-6 text-secondary">
                  Compare candidates with skills, evidence, and grounded AI.
                </p>
                <span className="mt-4 inline-flex text-sm font-semibold text-ai-muted">
                  Create employer account →
                </span>
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="border-t border-border bg-primary text-primary-foreground">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 sm:px-8 md:grid-cols-[1.2fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-3">
              <BrandMark />
              <span className="font-display text-sm font-semibold">BeyondResume</span>
            </div>
            <p className="mt-4 max-w-sm text-sm leading-6 text-primary-200">
              Evidence Intelligence for hiring — skills linked to proof, decisions you can defend.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-wide text-accent">Product</p>
            <ul className="mt-3 space-y-2 text-sm text-primary-100">
              <li>
                <a href="#product" className="hover:text-white">
                  Evidence flow
                </a>
              </li>
              <li>
                <a href="#for-candidates" className="hover:text-white">
                  For candidates
                </a>
              </li>
              <li>
                <a href="#for-employers" className="hover:text-white">
                  For employers
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-wide text-accent">Account</p>
            <ul className="mt-3 space-y-2 text-sm text-primary-100">
              <li>
                <Link href="/login" className="hover:text-white">
                  Sign in
                </Link>
              </li>
              <li>
                <Link href="/register" className="hover:text-white">
                  Create account
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10">
          <p className="mx-auto max-w-7xl px-5 py-5 text-xs text-primary-300 sm:px-8">
            © {new Date().getFullYear()} BeyondResume. Evidence over assumptions.
          </p>
        </div>
      </footer>
    </main>
  );
}

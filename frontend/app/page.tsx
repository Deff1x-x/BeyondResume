"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { CandidateProfileSection } from "@/features/candidate-profile-section";
import { GitHubSection } from "@/features/github-section";
import { ResumeSection } from "@/features/resume-section";
import { SkillPassportSection } from "@/features/skill-passport-section";
import { useCurrentUser, useLogout } from "@/lib/auth/hooks";

export default function HomePage() {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();

  function onSignOutClick() {
    logout();
    router.push("/login");
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-16 lg:px-8">
        <p className="text-sm text-secondary" role="status">
          Loading your account…
        </p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-16 lg:px-8">
        <section className="max-w-2xl" aria-labelledby="public-home-title">
          <p className="text-sm font-medium text-primary">BeyondResume</p>
          <h1 id="public-home-title" className="mt-4 text-4xl font-semibold text-ink">
            Show what you can do, beyond the resume.
          </h1>
          <p className="mt-6 text-lg leading-8 text-secondary">
            Build an evidence-based professional profile that helps employers understand your
            verified skills, experience, and potential.
          </p>

          {isError ? (
            <p className="mt-6 text-sm text-danger" role="alert">
              We could not verify your session. Sign in to continue.
            </p>
          ) : null}

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="inline-flex min-h-control items-center justify-center rounded-button bg-primary px-6 text-sm font-medium text-white"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="inline-flex min-h-control items-center justify-center rounded-button border border-border bg-surface px-6 text-sm font-medium text-ink"
            >
              Register
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-16 lg:px-8">
      <header className="flex flex-col gap-6 border-b border-border pb-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-primary">BeyondResume</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">Candidate workspace</h1>
          <p className="mt-2 break-words text-sm text-secondary">
            Signed in as <span className="font-medium text-ink">{user.email}</span> · {user.role}
          </p>
        </div>
        <button
          type="button"
          onClick={onSignOutClick}
          className="min-h-control shrink-0 rounded-button border border-border bg-surface px-6 text-sm font-medium text-ink"
        >
          Logout
        </button>
      </header>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <CandidateProfileSection enabled={user.role === "candidate"} />
        <ResumeSection enabled={user.role === "candidate"} />
        <GitHubSection enabled={user.role === "candidate"} />
        <SkillPassportSection enabled={user.role === "candidate"} />
      </div>
    </main>
  );
}

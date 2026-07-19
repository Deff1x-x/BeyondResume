"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { isTokenResponse } from "@/lib/api/auth";
import { ApiClientError } from "@/lib/api/error";
import { useRegister } from "@/lib/auth/hooks";

const VERIFICATION_MESSAGE =
  "Check your email to verify your account before signing in.";

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    try {
      const result = await registerMutation.mutateAsync({
        email,
        password,
        password_confirmation: passwordConfirmation,
        role: "candidate",
        terms_accepted: termsAccepted,
        privacy_accepted: privacyAccepted
      });

      if (!isTokenResponse(result)) {
        setInfoMessage(VERIFICATION_MESSAGE);
        return;
      }

      router.push("/");
    } catch (error) {
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
        return;
      }

      setErrorMessage("Something went wrong. Please try again.");
    }
  }

  const isSubmitting = registerMutation.isPending;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-16">
      <h1 className="text-2xl font-semibold text-ink">Create account</h1>
      <p className="mt-2 text-sm text-secondary">Register as a candidate to continue.</p>

      <form className="mt-8 space-y-6" onSubmit={handleSubmit} noValidate>
        <div className="space-y-2">
          <label htmlFor="email" className="block text-sm font-medium text-ink">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={isSubmitting}
            className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-ink outline-none focus:border-primary"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium text-ink">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isSubmitting}
            className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-ink outline-none focus:border-primary"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password_confirmation" className="block text-sm font-medium text-ink">
            Confirm password
          </label>
          <input
            id="password_confirmation"
            name="password_confirmation"
            type="password"
            autoComplete="new-password"
            required
            value={passwordConfirmation}
            onChange={(event) => setPasswordConfirmation(event.target.value)}
            disabled={isSubmitting}
            className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-ink outline-none focus:border-primary"
          />
        </div>

        <div className="space-y-3">
          <label className="flex items-start gap-3 text-sm text-ink">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(event) => setTermsAccepted(event.target.checked)}
              disabled={isSubmitting}
              className="mt-1"
            />
            <span>I accept the Terms of Service</span>
          </label>
          <label className="flex items-start gap-3 text-sm text-ink">
            <input
              type="checkbox"
              checked={privacyAccepted}
              onChange={(event) => setPrivacyAccepted(event.target.checked)}
              disabled={isSubmitting}
              className="mt-1"
            />
            <span>I accept the Privacy Policy</span>
          </label>
        </div>

        {errorMessage ? (
          <p className="text-sm text-danger" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {infoMessage ? (
          <p className="text-sm text-secondary" role="status">
            {infoMessage}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="min-h-control w-full rounded-button bg-primary px-4 text-sm font-medium text-white disabled:opacity-60"
        >
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-secondary">
        Already registered?{" "}
        <Link href="/login" className="text-primary underline-offset-2 hover:underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}

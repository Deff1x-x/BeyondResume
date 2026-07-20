"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { BrandMark } from "@/components/ui/icon";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { isTokenResponse } from "@/lib/api/auth";
import { ApiClientError } from "@/lib/api/error";
import type { Role } from "@/lib/api/types/auth";
import { useRegister } from "@/lib/auth/hooks";

const VERIFICATION_MESSAGE =
  "Check your email to verify your account before signing in.";

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [role, setRole] = useState<Role>("candidate");
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
        role,
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
    <PageContainer narrow centered>
      <div className="mb-8 flex items-center gap-3"><BrandMark /><span className="text-sm font-semibold tracking-wide text-primary">BeyondResume</span></div>
      <PageHeader
        title="Create account"
        description="Register as a candidate or employer to continue."
        className="border-0 pb-0"
      />

      <Card className="mt-8">
        <CardContent className="p-5 sm:p-6">
          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            <fieldset className="space-y-2" disabled={isSubmitting}>
              <legend className="text-sm font-medium text-ink">Account type</legend>
              <div className="flex flex-wrap gap-4">
                <label className="inline-flex items-center gap-2 text-sm text-ink">
                  <input
                    type="radio"
                    name="role"
                    value="candidate"
                    checked={role === "candidate"}
                    onChange={() => setRole("candidate")}
                  />
                  Candidate
                </label>
                <label className="inline-flex items-center gap-2 text-sm text-ink">
                  <input
                    type="radio"
                    name="role"
                    value="employer"
                    checked={role === "employer"}
                    onChange={() => setRole("employer")}
                  />
                  Employer
                </label>
              </div>
            </fieldset>

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-ink">
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-ink">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password_confirmation" className="block text-sm font-medium text-ink">
                Confirm password
              </label>
              <Input
                id="password_confirmation"
                name="password_confirmation"
                type="password"
                autoComplete="new-password"
                required
                value={passwordConfirmation}
                onChange={(event) => setPasswordConfirmation(event.target.value)}
                disabled={isSubmitting}
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
              <EmptyState
                role="alert"
                title="Registration failed"
                description={errorMessage}
                className="py-4"
              />
            ) : null}

            {infoMessage ? (
              <EmptyState
                title="Verify your email"
                description={infoMessage}
                className="py-4"
              />
            ) : null}

            <Button type="submit" variant="primary" className="w-full" loading={isSubmitting}>
              Create account
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="mt-6 text-sm text-secondary">
        Already registered?{" "}
        <Link
          href="/login"
          className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        >
          Sign in
        </Link>
      </p>
    </PageContainer>
  );
}

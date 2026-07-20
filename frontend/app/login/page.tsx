"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { ApiClientError } from "@/lib/api/error";
import { useLogin } from "@/lib/auth/hooks";

export default function LoginPage() {
  const router = useRouter();
  const loginMutation = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    try {
      await loginMutation.mutateAsync({ email, password });
      router.push("/");
    } catch (error) {
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
        return;
      }

      setErrorMessage("Something went wrong. Please try again.");
    }
  }

  const isSubmitting = loginMutation.isPending;

  return (
    <PageContainer narrow centered>
      <PageHeader
        title="Sign in"
        description="Access your BeyondResume account."
        className="border-0 pb-0"
      />

      <Card className="mt-8">
        <CardContent className="p-5 sm:p-6">
          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
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
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isSubmitting}
              />
            </div>

            {errorMessage ? (
              <EmptyState
                role="alert"
                title="Sign in failed"
                description={errorMessage}
                className="py-4"
              />
            ) : null}

            <Button type="submit" variant="primary" className="w-full" loading={isSubmitting}>
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="mt-6 text-sm text-secondary">
        Need an account?{" "}
        <Link
          href="/register"
          className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2"
        >
          Register
        </Link>
      </p>
    </PageContainer>
  );
}

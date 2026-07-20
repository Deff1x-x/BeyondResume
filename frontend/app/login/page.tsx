"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordInput } from "@/components/auth/password-input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { BrandMark } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { ApiClientError } from "@/lib/api/error";
import { useLogin } from "@/lib/auth/hooks";

export default function LoginPage() {
  const router = useRouter();
  const loginMutation = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isSubmitting = loginMutation.isPending;
  const isFormValid = email.trim().length > 0 && password.length > 0;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isFormValid || isSubmitting) return;
    setErrorMessage(null);
    try { await loginMutation.mutateAsync({ email, password }); router.push("/"); }
    catch (error) { setErrorMessage(error instanceof ApiClientError ? error.message : "Something went wrong. Please try again."); }
  }

  return <AuthShell><div className="mb-7 flex items-center justify-between"><Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-secondary transition hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"><span aria-hidden="true">←</span> Back to landing</Link><div className="flex items-center gap-2 lg:hidden"><BrandMark className="h-8 w-8 rounded-lg" /><span className="text-sm font-semibold">BeyondResume</span></div></div><Card className="border-white/80 bg-surface/90 shadow-float backdrop-blur"><CardContent className="p-6 sm:p-8"><p className="text-sm font-semibold uppercase tracking-[.12em] text-primary">Welcome back</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink">Sign in to your workspace</h1><p className="mt-3 text-sm leading-6 text-secondary">Continue building the professional story behind your résumé.</p><form className="mt-8 space-y-5" onSubmit={handleSubmit} noValidate><div className="space-y-2"><label htmlFor="email" className="block text-sm font-medium text-ink">Email</label><Input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} disabled={isSubmitting} aria-invalid={Boolean(errorMessage)} aria-describedby={errorMessage ? "login-error" : undefined} /></div><div className="space-y-2"><label htmlFor="password" className="block text-sm font-medium text-ink">Password</label><PasswordInput id="password" name="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} disabled={isSubmitting} aria-invalid={Boolean(errorMessage)} aria-describedby={errorMessage ? "login-error" : undefined} /></div>{errorMessage ? <p id="login-error" role="alert" className="rounded-xl border border-danger/20 bg-danger/5 px-3 py-3 text-sm text-danger">{errorMessage}</p> : null}<Button type="submit" variant="primary" className="w-full" loading={isSubmitting} disabled={!isFormValid}>Sign in</Button></form><p className="mt-6 text-center text-sm text-secondary">New to BeyondResume? <Link href="/register" className="font-semibold text-primary hover:underline">Create an account</Link></p></CardContent></Card><p className="mt-6 text-center text-xs leading-5 text-secondary lg:hidden">Evidence-based profiles. Transparent matching. No résumé guesswork.</p></AuthShell>;
}

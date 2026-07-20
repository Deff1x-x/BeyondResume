"use client";

import { useState, type InputHTMLAttributes } from "react";
import { Input } from "@/components/ui/input";

type PasswordInputProps = InputHTMLAttributes<HTMLInputElement>;

export function PasswordInput({ className, ...props }: Readonly<PasswordInputProps>) {
  const [visible, setVisible] = useState(false);
  return <div className="relative"><Input {...props} type={visible ? "text" : "password"} className={`pr-12 ${className ?? ""}`} /><button type="button" onClick={() => setVisible((value) => !value)} disabled={props.disabled} aria-label={visible ? "Hide password" : "Show password"} className="absolute inset-y-0 right-0 inline-flex w-11 items-center justify-center text-secondary transition hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring disabled:cursor-not-allowed disabled:text-muted"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true" className="h-5 w-5"><path d={visible ? "M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 4.2A10.6 10.6 0 0 1 12 4c5.5 0 9.5 4.4 10 8-.2 1.4-.9 2.8-2 4M6.5 6.5C4.4 8 2.6 10.2 2 12c.5 3.6 4.5 8 10 8 1.6 0 3-.4 4.3-1.1" : "M2 12s3.5-8 10-8 10 8 10 8-3.5 8-10 8S2 12 2 12Z"} /><circle cx="12" cy="12" r="3" className={visible ? "hidden" : ""} /></svg></button></div>;
}

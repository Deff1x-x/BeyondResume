"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/ui/icon";
import { useLogout } from "@/lib/auth/hooks";

export function WorkspaceNavigation({ role }: Readonly<{ role: "candidate" | "employer" }>) {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useLogout();
  const links = role === "candidate" ? [{ href: "/", label: "Dashboard" }, { href: "/profile", label: "Profile" }] : [{ href: "/", label: "Workspace" }];
  return <div className="mb-10 flex flex-col gap-4 border-b border-border/80 pb-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex flex-wrap items-center gap-x-7 gap-y-3"><Link href="/" className="flex items-center gap-2"><BrandMark /><span className="text-sm font-semibold text-ink">BeyondResume</span></Link><nav className="flex items-center gap-1" aria-label="Workspace navigation">{links.map((link) => <Link key={link.href} href={link.href} className={`rounded-lg px-3 py-2 text-sm font-medium transition ${pathname === link.href ? "bg-primary/10 text-primary" : "text-secondary hover:text-ink"}`}>{link.label}</Link>)}</nav></div><Button type="button" variant="secondary" onClick={() => { logout(); router.push("/login"); }}>Logout</Button></div>;
}

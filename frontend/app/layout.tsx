import "../styles/globals.css";

import { Providers } from "@/app/providers";

import { Manrope, Plus_Jakarta_Sans } from "next/font/google";

import type { Metadata } from "next";
import type { ReactNode } from "react";

const sans = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap"
});

const display = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap"
});

export const metadata: Metadata = {
  title: "BeyondResume",
  icons: {
    icon: [{ url: "/brand/beyondresume-logo.jpg", type: "image/jpeg" }],
    apple: [{ url: "/brand/beyondresume-logo.jpg", type: "image/jpeg" }]
  }
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable}`}>
      <body className="font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

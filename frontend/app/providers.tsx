"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Limited retries: avoid hammering auth/validation failures.
        retry: 1,
        // Avoid surprise refetch storms while forms/poll flows are added later.
        refetchOnWindowFocus: false
      },
      mutations: {
        retry: false
      }
    }
  });
}

export function Providers({ children }: Readonly<{ children: ReactNode }>) {
  const [queryClient] = useState(createQueryClient);

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

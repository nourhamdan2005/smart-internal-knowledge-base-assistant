"use client"

import { useState, type ReactNode } from "react"
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { shouldRetryApiError } from "@/lib/api/client"

const STALE_TIME_MS = 30_000
const GARBAGE_COLLECTION_TIME_MS = 5 * 60_000

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: STALE_TIME_MS,
        gcTime: GARBAGE_COLLECTION_TIME_MS,
        retry: shouldRetryApiError,
        retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 4_000),
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

export function QueryProvider({
  children,
}: Readonly<{ children: ReactNode }>) {
  const [queryClient] = useState(createQueryClient)

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

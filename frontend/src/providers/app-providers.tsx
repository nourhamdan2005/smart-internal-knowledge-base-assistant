"use client"

import type { ReactNode } from "react"

import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { QueryProvider } from "@/providers/query-provider"
import { ThemeProvider } from "@/providers/theme-provider"
import { AuthProvider } from "@/features/auth"
import { PreferencesProvider } from "@/features/preferences"

export function AppProviders({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <ThemeProvider>
      <PreferencesProvider>
        <QueryProvider>
          <AuthProvider>
            <TooltipProvider delay={250}>
              {children}
              <Toaster position="top-right" closeButton richColors />
            </TooltipProvider>
          </AuthProvider>
        </QueryProvider>
      </PreferencesProvider>
    </ThemeProvider>
  )
}

"use client"

import { SidebarProvider } from "@/components/ui/sidebar"
import { useAuth } from "@/features/auth"
import { usePreferences } from "@/features/preferences"

import { AppHeader } from "./app-header"
import { AppSidebar } from "./app-sidebar"
import { PageTransition } from "./page-transition"
import { OfflineBanner } from "./offline-banner"

export function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const { user } = useAuth()
  const { preferences, hydrated } = usePreferences()
  if (!user) return null

  return (
    <SidebarProvider
      key={`${hydrated}-${preferences.sidebarExpanded}`}
      defaultOpen={preferences.sidebarExpanded}
    >
      <a
        href="#main-content"
        className="fixed left-4 top-4 z-[100] -translate-y-20 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-lg transition-transform focus:translate-y-0"
      >
        Skip to main content
      </a>
      <AppSidebar session={user} />
      <div className="flex min-h-svh min-w-0 flex-1 flex-col overflow-x-hidden bg-background">
        <OfflineBanner />
        <AppHeader session={user} />
        <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </SidebarProvider>
  )
}

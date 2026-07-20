import { AppBreadcrumbs } from "./app-breadcrumbs"
import { AppUserMenu } from "./app-user-menu"

import { ThemeToggle } from "@/components/theme-toggle"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import type { AuthenticatedUser } from "@/features/auth"

export function AppHeader({
  session,
}: Readonly<{ session: AuthenticatedUser }>) {
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b bg-background/88 px-2 backdrop-blur-xl sm:gap-3 sm:px-5">
      <SidebarTrigger aria-label="Toggle application navigation" />
      <Separator orientation="vertical" className="h-5" />
      <div className="min-w-0 flex-1">
        <AppBreadcrumbs />
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <ThemeToggle />
        <AppUserMenu session={session} />
      </div>
    </header>
  )
}

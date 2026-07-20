"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

import { ErrorState, LoadingState } from "@/components/design-system/feedback"
import { Button } from "@/components/ui/button"
import { APP_ROUTES, ROUTE_ACCESS, type AppRoute, type Permission } from "@/constants"

import { useAuth } from "./auth-provider"

export function AuthBoundary({ children }: Readonly<{ children: React.ReactNode }>) {
  const { status, hasPermission, refreshCurrentUser } = useAuth()
  const pathname = usePathname()
  const router = useRouter()
  const routeAccess: Partial<Record<AppRoute, Permission>> = ROUTE_ACCESS
  const requiredPermission = routeAccess[pathname as AppRoute]
  const forbidden = status === "authenticated" &&
    requiredPermission !== undefined &&
    !hasPermission(requiredPermission)

  useEffect(() => {
    if (status === "unauthenticated") {
      const returnTo = pathname.startsWith("/") ? pathname : APP_ROUTES.dashboard
      router.replace(`${APP_ROUTES.login}?returnTo=${encodeURIComponent(returnTo)}`)
    }
  }, [pathname, router, status])

  if (status === "initializing" || status === "unauthenticated") {
    return <LoadingState fullPage label="Verifying your secure session" />
  }

  if (status === "unavailable") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <ErrorState
          title="Session verification is temporarily unavailable"
          description="Your saved session was preserved, but the authentication service could not be reached."
          action={<Button onClick={() => void refreshCurrentUser()}>Retry verification</Button>}
        />
      </div>
    )
  }

  if (forbidden) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <ErrorState
          title="Access restricted"
          description="Your account does not have permission to open this workspace area."
          action={<Button onClick={() => router.push(APP_ROUTES.dashboard)}>Return to dashboard</Button>}
        />
      </div>
    )
  }

  return children
}

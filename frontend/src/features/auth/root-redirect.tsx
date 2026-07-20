"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { LoadingState } from "@/components/design-system/feedback"
import { APP_ROUTES } from "@/constants"

import { useAuth } from "./auth-provider"

export function RootRedirect() {
  const { status } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (status === "authenticated") {
      router.replace(APP_ROUTES.dashboard)
    } else if (status === "unauthenticated") {
      router.replace(APP_ROUTES.login)
    }
  }, [router, status])

  return <LoadingState fullPage label="Opening CGC Knowledge AI" />
}

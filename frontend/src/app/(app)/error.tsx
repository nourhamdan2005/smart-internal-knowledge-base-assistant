"use client"

import { useEffect } from "react"

import { ErrorState } from "@/components/design-system/feedback"
import { Button } from "@/components/ui/button"

export default function AuthenticatedError({
  error,
  unstable_retry,
}: Readonly<{
  error: Error & { digest?: string }
  unstable_retry: () => void
}>) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <ErrorState
        title="This workspace view could not be loaded"
        description="The application shell is still available. Retry the current route, or use the navigation to continue elsewhere."
        action={<Button onClick={unstable_retry}>Try this page again</Button>}
      />
    </div>
  )
}

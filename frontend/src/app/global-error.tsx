"use client"

import { useEffect } from "react"

import { ErrorState } from "@/components/design-system/feedback"
import { Button } from "@/components/ui/button"

export default function GlobalError({
  error,
  reset,
}: Readonly<{ error: Error & { digest?: string }; reset: () => void }>) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <html lang="en">
      <body className="bg-background text-foreground">
        <main className="mx-auto flex min-h-svh max-w-3xl items-center px-4 py-16 sm:px-6">
          <ErrorState
            title="CGC Knowledge AI could not start"
            description="A critical application error interrupted startup. Retry once; if it continues, contact your system administrator."
            action={<Button onClick={reset}>Restart application</Button>}
          />
        </main>
      </body>
    </html>
  )
}

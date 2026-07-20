import Link from "next/link"

import { EmptyState } from "@/components/design-system/feedback"
import { Button } from "@/components/ui/button"
import { APP_ROUTES } from "@/constants/routes"

export default function AuthenticatedNotFound() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <EmptyState
        title="Workspace page not found"
        description="The requested authenticated page does not exist or may have moved."
        action={
          <Button nativeButton={false} render={<Link href={APP_ROUTES.dashboard} />}>
            Return to dashboard
          </Button>
        }
      />
    </div>
  )
}

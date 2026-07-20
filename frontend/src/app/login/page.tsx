import { Suspense } from "react"

import { LoadingState } from "@/components/design-system/feedback"
import { LoginForm } from "@/features/auth/login-form"

export default function LoginPage() {
  return (
    <Suspense fallback={<LoadingState fullPage label="Preparing secure sign in" />}>
      <LoginForm />
    </Suspense>
  )
}

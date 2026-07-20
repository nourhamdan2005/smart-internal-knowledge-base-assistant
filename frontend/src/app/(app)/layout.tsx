import { AppShell } from "@/components/app-shell"
import { AuthBoundary } from "@/features/auth/auth-boundary"

export default function AuthenticatedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <AuthBoundary>
      <AppShell>{children}</AppShell>
    </AuthBoundary>
  )
}

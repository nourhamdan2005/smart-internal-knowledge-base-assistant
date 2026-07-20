"use client"

import Link from "next/link"
import { KeyRound, ShieldCheck, UserRound } from "lucide-react"

import { AppPageContainer, UserIdentity } from "@/components/app-shell"
import { EmptyState } from "@/components/design-system/feedback"
import { MetadataList, PageHeader, SectionHeader } from "@/components/design-system/layout"
import { RoleBadge, StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { APP_ROUTES, PERMISSIONS } from "@/constants"
import { useAuth } from "@/features/auth"

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "Never"
}

export function ProfileView() {
  const { user, hasPermission } = useAuth()
  if (!user) return null

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Review the identity and account state reported by the authentication service."
      />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserRound className="size-4 text-primary" />
              Authenticated identity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <UserIdentity user={user} showRole />
            <div className="flex flex-wrap gap-2">
              <RoleBadge role={user.role} />
              <StatusBadge tone={user.isActive ? "success" : "danger"}>
                {user.isActive ? "Active account" : "Inactive account"}
              </StatusBadge>
            </div>
            <MetadataList
              items={[
                { label: "Full name", value: user.fullName },
                { label: "Email", value: <span className="break-all">{user.email}</span> },
                { label: "User ID", value: <span className="break-all font-mono text-xs">{user.id}</span> },
                { label: "Created", value: formatDate(user.createdAt) },
                { label: "Updated", value: formatDate(user.updatedAt) },
                { label: "Last login", value: formatDate(user.lastLoginAt) },
              ]}
            />
          </CardContent>
        </Card>
        <div className="space-y-6">
          <Card>
            <CardHeader><SectionHeader title="Account security" icon={ShieldCheck} /></CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">
              Your session uses JWT authentication. Passwords are Argon2-hashed by the backend and are never returned to this application.
            </CardContent>
          </Card>
          <EmptyState
            compact
            title="Profile changes are administrator-managed"
            description="The backend does not provide a self-service profile or password-change endpoint."
            action={hasPermission(PERMISSIONS.usersManage) ? (
              <Button nativeButton={false} variant="outline" render={<Link href={APP_ROUTES.users} />}>
                <KeyRound />Open User Management
              </Button>
            ) : undefined}
          />
        </div>
      </div>
    </AppPageContainer>
  )
}

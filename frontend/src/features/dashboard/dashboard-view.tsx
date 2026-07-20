"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Activity, Bot, FileText, HardDriveUpload, Library, Users, Wrench } from "lucide-react"

import { AppPageContainer } from "@/components/app-shell"
import { EmptyState, ErrorState } from "@/components/design-system/feedback"
import { PageHeader, SectionHeader } from "@/components/design-system/layout"
import { CardSkeleton } from "@/components/design-system/loading"
import { StaggeredItem, StaggeredList } from "@/components/design-system/motion"
import { FeatureCard, GlassPanel, StatCard } from "@/components/design-system/surfaces"
import { RoleBadge, StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { APP_ROUTES, PERMISSIONS } from "@/constants"
import { useAuth } from "@/features/auth"
import { chatHistoryStorage } from "@/features/ai-chat/storage"

import {
  dashboardKeys,
  getDashboardDocuments,
  getDashboardUsers,
  getReadiness,
} from "./api"

const suggestedQuestions = [
  "What is our remote-work policy?",
  "How should I report a security incident?",
  "Summarize the employee onboarding procedure.",
  "What are the password and MFA requirements?",
]

export function DashboardView() {
  const { user, hasPermission } = useAuth()
  const canUpload = hasPermission(PERMISSIONS.uploadsView)
  const canManageUsers = hasPermission(PERMISSIONS.usersView)
  const [recentQuestions, setRecentQuestions] = useState<string[]>([])
  const [greeting, setGreeting] = useState("Welcome back")
  const documents = useQuery({
    queryKey: dashboardKeys.documents(),
    queryFn: ({ signal }) => getDashboardDocuments(signal),
    staleTime: 60_000,
  })
  const users = useQuery({
    queryKey: dashboardKeys.users(),
    queryFn: ({ signal }) => getDashboardUsers(signal),
    enabled: canManageUsers,
    staleTime: 60_000,
  })
  const health = useQuery({
    queryKey: dashboardKeys.health(),
    queryFn: ({ signal }) => getReadiness(signal),
    enabled: canManageUsers,
    staleTime: 30_000,
    retry: false,
  })

  useEffect(() => {
    if (!user) return
    const frame = requestAnimationFrame(() => {
      const questions = chatHistoryStorage
        .load(user.id)
        .flatMap((conversation) => conversation.messages)
        .filter((message) => message.role === "user")
        .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
        .slice(0, 4)
        .map((message) => message.content)
      setRecentQuestions(questions)
    })
    return () => cancelAnimationFrame(frame)
  }, [user])

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const hour = new Date().getHours()
      setGreeting(hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening")
    })
    return () => cancelAnimationFrame(frame)
  }, [])

  if (!user) return null
  const activeDocuments = documents.data?.filter((document) => document.is_active) ?? []
  const categories = [...new Set(activeDocuments.map((document) => document.category))].slice(0, 6)
  const recentDocuments = activeDocuments.slice(0, 5)
  const activeUsers = users.data?.filter((account) => account.is_active).length

  return (
    <AppPageContainer className="space-y-8">
      <PageHeader
        eyebrow="Knowledge workspace"
        title={`${greeting}, ${user.fullName.split(" ")[0]}`}
        description="Find trusted company knowledge, ask grounded questions, and access the tools available to your role."
        actions={<><RoleBadge role={user.role} /><Button nativeButton={false} size="lg" render={<Link href={APP_ROUTES.chat} />}><Bot />Ask CGC AI</Button></>}
      />

      <GlassPanel className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-heading text-xl font-semibold">What would you like to know?</h2>
          <p className="mt-2 text-sm text-muted-foreground">Answers are grounded in approved internal documents and include source citations.</p>
        </div>
        <Button nativeButton={false} size="lg" render={<Link href={APP_ROUTES.chat} />}><Bot />Start a conversation</Button>
      </GlassPanel>

      {documents.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : documents.isError ? (
        <ErrorState title="Documents are temporarily unavailable" description="The rest of your workspace remains available. Try refreshing this section shortly." />
      ) : (
        <StaggeredList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {canUpload && <StaggeredItem><StatCard label="Available documents" value={activeDocuments.length} icon={FileText} change="Current active knowledge sources" /></StaggeredItem>}
          {canManageUsers && <StaggeredItem><StatCard label="Active users" value={users.isError ? "Unavailable" : activeUsers ?? "—"} icon={Users} change={users.isError ? "User data could not be loaded" : `${users.data?.length ?? 0} total accounts`} /></StaggeredItem>}
          {canManageUsers && <StaggeredItem><StatCard label="System readiness" value={health.isError ? "Unavailable" : health.data?.status ?? "Checking"} icon={Activity} change={health.isError ? "Readiness could not be loaded" : health.data?.message ?? "Checking service readiness"} /></StaggeredItem>}
        </StaggeredList>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeader><CardTitle>Recently available documents</CardTitle></CardHeader>
          <CardContent>
            {recentDocuments.length === 0 ? (
              <EmptyState compact title="No documents available" description="Documents accessible to your account will appear here." />
            ) : (
              <ul className="divide-y">
                {recentDocuments.map((document) => (
                  <li key={document.id} className="flex items-center justify-between gap-4 py-3.5">
                    <div className="min-w-0"><p className="truncate text-sm font-medium" title={document.title}>{document.title}</p><p className="mt-1 text-xs text-muted-foreground">{document.author}</p></div>
                    <StatusBadge tone="neutral">{document.category}</StatusBadge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Suggested questions</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {suggestedQuestions.map((question) => (
              <Button nativeButton={false} key={question} variant="outline" className="h-auto w-full justify-start whitespace-normal border-primary/10 bg-primary/[0.03] p-3 text-left hover:border-primary/25 hover:bg-primary/[0.07]" render={<Link href={`${APP_ROUTES.chat}?prompt=${encodeURIComponent(question)}`} />}><Bot className="mt-0.5 shrink-0" />{question}</Button>
            ))}
          </CardContent>
        </Card>
      </div>

      {recentQuestions.length > 0 && (
        <section className="space-y-4">
          <SectionHeader title="Recently asked on this device" description="User-scoped local history; not yet synchronized with the server." />
          <div className="grid gap-3 sm:grid-cols-2">
            {recentQuestions.map((question, index) => (
  <Button
    nativeButton={false}
    key={`${question}-${index}`}
    variant="outline"
    className="h-auto justify-start whitespace-normal p-4 text-left"
    render={<Link href={`${APP_ROUTES.chat}?prompt=${encodeURIComponent(question)}`} />}
  >
    {question}
  </Button>
))}
          </div>
        </section>
      )}

      <section className="space-y-4">
        <SectionHeader title="Quick actions" description="Actions are filtered by your current permissions." />
        <StaggeredList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StaggeredItem><FeatureCard icon={Library} title="Browse documents" description="Explore the current company knowledge catalog." footer={<Button nativeButton={false} variant="outline" render={<Link href={APP_ROUTES.documents} />}>Open documents</Button>} /></StaggeredItem>
          {canUpload && <StaggeredItem><FeatureCard icon={HardDriveUpload} title="Upload documents" description="Add approved content to the ingestion pipeline." footer={<Button nativeButton={false} variant="outline" render={<Link href={APP_ROUTES.uploadCenter} />}>Open uploads</Button>} /></StaggeredItem>}
          {canManageUsers && <StaggeredItem><FeatureCard icon={Users} title="Manage users" description="Review accounts, roles, and access state." footer={<Button nativeButton={false} variant="outline" render={<Link href={APP_ROUTES.users} />}>Open users</Button>} /></StaggeredItem>}
          {canManageUsers && <StaggeredItem><FeatureCard icon={Wrench} title="Maintenance" description="Access authorized administrative operations." footer={<Button nativeButton={false} variant="outline" render={<Link href={APP_ROUTES.maintenance} />}>Open maintenance</Button>} /></StaggeredItem>}
        </StaggeredList>
      </section>

      {categories.length > 0 && (
        <section className="space-y-4">
          <SectionHeader title="Browse by category" />
          <div className="flex flex-wrap gap-2">{categories.map((category) => <Button nativeButton={false} key={category} variant="outline" render={<Link href={`${APP_ROUTES.documents}?category=${encodeURIComponent(category)}`} />}>{category}</Button>)}</div>
        </section>
      )}
    </AppPageContainer>
  )
}

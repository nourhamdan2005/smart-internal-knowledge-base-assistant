"use client"

import { useQuery } from "@tanstack/react-query"
import { Activity, Database, RefreshCw, Server } from "lucide-react"

import { AppPageContainer } from "@/components/app-shell"
import { ErrorState } from "@/components/design-system/feedback"
import { PageHeader } from "@/components/design-system/layout"
import { CardSkeleton } from "@/components/design-system/loading"
import { HealthIndicator } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import { getHealth, getReadiness, maintenanceKeys } from "./api"

function checkedAt(timestamp: number) {
  return timestamp
    ? new Intl.DateTimeFormat(undefined, { timeStyle: "medium" }).format(timestamp)
    : "Not checked"
}

export function SystemHealthView() {
  const health = useQuery({
    queryKey: maintenanceKeys.health(),
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30_000,
  })
  const readiness = useQuery({
    queryKey: maintenanceKeys.readiness(),
    queryFn: ({ signal }) => getReadiness(signal),
    refetchInterval: 30_000,
  })
  const refresh = () => void Promise.all([health.refetch(), readiness.refetch()])

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader
        eyebrow="Operations"
        title="System Health"
        description="Live service and retrieval-infrastructure status reported by the backend."
        actions={<Button variant="outline" onClick={refresh} disabled={health.isFetching || readiness.isFetching}><RefreshCw className={health.isFetching || readiness.isFetching ? "animate-spin motion-reduce:animate-none" : ""} />Refresh</Button>}
      />
      {health.isLoading || readiness.isLoading ? (
        <div className="grid gap-4 md:grid-cols-3"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : health.isError && readiness.isError ? (
        <ErrorState title="Health checks are unavailable" description="The application could not reach either backend health endpoint." action={<Button onClick={refresh}>Retry</Button>} />
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Server className="size-4 text-primary" />API service</CardTitle></CardHeader><CardContent className="space-y-3"><HealthIndicator status={health.data?.status === "ok" ? "healthy" : "offline"} label={health.data?.status === "ok" ? "Operational" : "Unavailable"} /><p className="text-sm text-muted-foreground">{health.data?.message ?? "No response was received."}</p><p className="text-xs text-muted-foreground">Checked {checkedAt(health.dataUpdatedAt)}</p></CardContent></Card>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="size-4 text-primary" />Readiness</CardTitle></CardHeader><CardContent className="space-y-3"><HealthIndicator status={readiness.data?.status === "ok" ? "healthy" : readiness.data?.status === "degraded" ? "degraded" : "offline"} label={readiness.data?.status === "ok" ? "Ready" : readiness.data?.status === "degraded" ? "Degraded" : "Not ready"} /><p className="text-sm text-muted-foreground">{readiness.data?.message ?? "No response was received."}</p><p className="text-xs text-muted-foreground">Checked {checkedAt(readiness.dataUpdatedAt)}</p></CardContent></Card>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Database className="size-4 text-primary" />Vector database</CardTitle></CardHeader><CardContent className="space-y-3"><HealthIndicator status={readiness.data?.qdrant === "ready" ? "healthy" : readiness.data?.qdrant === "disabled" ? "disabled" : "offline"} label={readiness.data?.qdrant === "ready" ? "Ready" : readiness.data?.qdrant === "disabled" ? "Disabled" : "Unavailable"} /><p className="text-sm text-muted-foreground">Qdrant status is reported by the readiness endpoint.</p><p className="text-xs text-muted-foreground">Checked {checkedAt(readiness.dataUpdatedAt)}</p></CardContent></Card>
        </div>
      )}
    </AppPageContainer>
  )
}

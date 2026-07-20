"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Blocks, DatabaseZap, RefreshCw } from "lucide-react"
import { toast } from "sonner"

import { AppPageContainer } from "@/components/app-shell"
import { ConfirmActionDialog, ErrorState, InlineSpinner } from "@/components/design-system/feedback"
import { MetadataList, PageHeader } from "@/components/design-system/layout"
import { StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { dashboardKeys } from "@/features/dashboard/api"
import { documentKeys } from "@/features/documents/api"
import type { NormalizedApiError } from "@/lib/api/client"

import { maintenanceKeys, runMaintenance } from "./api"
import type { MaintenanceOperation, MaintenanceResult } from "./types"

const operations = [
  { id: "chunks" as const, title: "Backfill chunks", description: "Create missing searchable chunks for existing active documents.", icon: Blocks },
  { id: "embeddings" as const, title: "Backfill embeddings", description: "Generate missing semantic embeddings for eligible chunks.", icon: RefreshCw },
  { id: "vectors" as const, title: "Backfill vectors", description: "Upsert eligible embedded chunks into the configured vector collection.", icon: DatabaseZap },
]

function summarize(result: MaintenanceResult) {
  return Object.entries(result)
    .filter(([key, value]) => key !== "failures" && key !== "errors" && typeof value !== "object")
    .map(([key, value]) => ({ label: key.replaceAll("_", " "), value: String(value) }))
}

function resultErrors(result: MaintenanceResult) {
  if ("errors" in result) return result.errors
  return result.failures.map((failure) => failure.error)
}

export function MaintenanceView() {
  const queryClient = useQueryClient()
  const [history, setHistory] = useState<Array<{ operation: MaintenanceOperation; result: MaintenanceResult; at: Date }>>([])
  const mutation = useMutation<MaintenanceResult, NormalizedApiError, MaintenanceOperation>({
    mutationFn: runMaintenance,
    onSuccess: async (result, operation) => {
      setHistory((current) => [{ operation, result, at: new Date() }, ...current])
      toast.success(`${operation} backfill completed.`)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: maintenanceKeys.all }),
        queryClient.invalidateQueries({ queryKey: dashboardKeys.health() }),
        queryClient.invalidateQueries({ queryKey: dashboardKeys.documents() }),
        queryClient.invalidateQueries({ queryKey: documentKeys.all }),
      ])
    },
    onError: (error) => toast.error(error.message),
  })

  return (
    <AppPageContainer className="space-y-8">
      <PageHeader eyebrow="Administration" title="Maintenance" description="Run supported indexing backfills. Operations execute immediately and may take several minutes." />
      <div className="grid gap-4 lg:grid-cols-3">
        {operations.map(({ id, title, description, icon: Icon }) => (
          <Card key={id}>
            <CardHeader><span className="mb-2 flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary"><Icon className="size-5" /></span><CardTitle>{title}</CardTitle><CardDescription>{description}</CardDescription></CardHeader>
            <CardContent>
              <ConfirmActionDialog
                trigger={<Button className="w-full" disabled={mutation.isPending}>{mutation.isPending && mutation.variables === id ? <InlineSpinner label={`Running ${title}`} /> : <RefreshCw />}Run operation</Button>}
                title={`Run ${title.toLowerCase()}?`}
                description="This writes derived retrieval data for existing records. Do not close the application until the request completes."
                confirmLabel="Run backfill"
                onConfirm={() => mutation.mutate(id)}
              />
            </CardContent>
          </Card>
        ))}
      </div>
      {mutation.isError && <ErrorState compact title="Maintenance operation failed" description={mutation.error.message} />}
      <section className="space-y-4">
        <div><h2 className="font-heading text-xl font-semibold">This-session results</h2><p className="text-sm text-muted-foreground">The backend does not persist maintenance history; these results remain only until this page reloads.</p></div>
        {history.length === 0 ? <p className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">No maintenance operations have run in this browser session.</p> : history.map((entry) => {
          const errors = resultErrors(entry.result)
          return <Card key={`${entry.operation}-${entry.at.toISOString()}`}><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="capitalize">{entry.operation} backfill</CardTitle><StatusBadge tone={errors.length ? "warning" : "success"}>{errors.length ? "Completed with errors" : "Completed"}</StatusBadge></div><CardDescription>{entry.at.toLocaleString()}</CardDescription></CardHeader><CardContent className="space-y-4"><MetadataList items={summarize(entry.result)} />{errors.length > 0 && <div role="alert" className="rounded-xl border border-warning/20 bg-warning/5 p-4"><p className="font-medium text-warning">Reported errors</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">{errors.map((error, index) => <li key={`${error}-${index}`}>{error}</li>)}</ul></div>}</CardContent></Card>
        })}
      </section>
    </AppPageContainer>
  )
}

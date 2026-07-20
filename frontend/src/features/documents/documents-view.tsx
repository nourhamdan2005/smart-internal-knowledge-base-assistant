"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Bot, Grid2X2, List, Pencil, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { AppPageContainer } from "@/components/app-shell"
import { DataViewToolbar, MobileCardFallback, PaginationControls, ResponsiveDataTableContainer, SearchField } from "@/components/design-system/data-view"
import { ConfirmActionDialog, EmptyState, ErrorState } from "@/components/design-system/feedback"
import { FormSection, SelectField, SubmitButton, TextField } from "@/components/design-system/forms"
import { MetadataList, PageHeader } from "@/components/design-system/layout"
import { TableSkeleton } from "@/components/design-system/loading"
import { StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { APP_ROUTES, PERMISSIONS } from "@/constants"
import { useAuth } from "@/features/auth"
import { dashboardKeys } from "@/features/dashboard/api"
import { usePreferences } from "@/features/preferences"

import { deleteDocument, documentKeys, listDocuments, updateDocument } from "./api"
import { DOCUMENT_CATEGORIES, type DocumentRecord } from "./types"

function formatBytes(value: number | null) {
  if (value === null) return "Unavailable"
  if (value < 1024) return `${value} B`
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 ** 2).toFixed(1)} MB`
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value)) : "Unavailable"
}

export function DocumentsView() {
  const router = useRouter()
  const params = useSearchParams()
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const { preferences, updatePreference } = usePreferences()
  const canEdit = hasPermission(PERMISSIONS.documentsUpdate)
  const canDelete = hasPermission(PERMISSIONS.documentsDelete)
  const [searchInput, setSearchInput] = useState(params.get("search") ?? "")
  const [view, setView] = useState<"table" | "grid">(preferences.documentView)
  const [selected, setSelected] = useState<DocumentRecord | null>(null)
  const [editing, setEditing] = useState<DocumentRecord | null>(null)
  const [editCategory, setEditCategory] = useState<DocumentRecord["category"]>("HR")
  const category = params.get("category") ?? ""
  const sort = params.get("sort") ?? "-created_at"
  const page = Math.max(1, Number(params.get("page") ?? 1))
  const limit = preferences.pageSize

  function updateParams(changes: Record<string, string | number | null>) {
    const next = new URLSearchParams(params.toString())
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === "") next.delete(key)
      else next.set(key, String(value))
    }
    router.replace(`${APP_ROUTES.documents}?${next.toString()}`)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => updateParams({ search: searchInput, page: 1 }), 350)
    return () => window.clearTimeout(timer)
  // URL params intentionally update only after the debounced input changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput])

  const filters = useMemo(() => ({ search: params.get("search") ?? "", category, sort, page, limit }), [category, limit, page, params, sort])
  const documents = useQuery({
    queryKey: documentKeys.list(filters),
    queryFn: ({ signal }) => listDocuments(filters, signal),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  })
  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: documentKeys.all }),
      queryClient.invalidateQueries({ queryKey: dashboardKeys.documents() }),
    ])
  }
  const editMutation = useMutation({
    mutationFn: ({ id, title, category: nextCategory }: { id: string; title: string; category: DocumentRecord["category"] }) =>
      updateDocument(id, { title, category: nextCategory }),
    onSuccess: async (updated) => {
      toast.success("Document updated.")
      setEditing(null)
      setSelected(updated)
      await invalidate()
    },
    onError: (error) => toast.error(error.message),
  })
  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: async () => {
      toast.success("Document removed from searchable knowledge.")
      setSelected(null)
      await invalidate()
    },
    onError: (error) => toast.error(error.message),
  })
  const rows = documents.data ?? []

  const actions = (document: DocumentRecord) => (
    <div className="flex flex-wrap gap-2">
      <Button nativeButton={false} size="sm" variant="outline" render={<Link href={`${APP_ROUTES.chat}?prompt=${encodeURIComponent(`What should I know about "${document.title}"?`)}&category=${encodeURIComponent(document.category)}`} />}><Bot />Ask AI</Button>
      {canEdit && <Button size="sm" variant="outline" onClick={() => { setEditing(document); setEditCategory(document.category) }}><Pencil />Edit</Button>}
      {canDelete && <ConfirmActionDialog trigger={<Button size="sm" variant="destructive"><Trash2 />Delete</Button>} title={`Delete “${document.title}”?`} description="This removes the document and its chunks from searchable company knowledge." destructive confirmLabel="Delete document" onConfirm={() => deleteMutation.mutate(document.id)} />}
    </div>
  )

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader eyebrow="Knowledge catalog" title="Documents" description="Browse the active internal sources available to your account." actions={canEdit ? <Button nativeButton={false} render={<Link href={APP_ROUTES.uploadCenter} />}><Plus />Upload document</Button> : undefined} />
      <DataViewToolbar
        search={<SearchField label="Search title, content, or tags" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} />}
        filters={<div className="flex min-w-max gap-2">
          <Select value={category || "all"} onValueChange={(value) => updateParams({ category: value === "all" ? null : value, page: 1 })}><SelectTrigger aria-label="Filter by category" className="w-40"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All categories</SelectItem>{DOCUMENT_CATEGORIES.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}</SelectContent></Select>
          <Select value={sort} onValueChange={(value) => updateParams({ sort: value, page: 1 })}><SelectTrigger aria-label="Sort documents" className="w-44"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="-created_at">Newest created</SelectItem><SelectItem value="created_at">Oldest created</SelectItem><SelectItem value="title">Title A–Z</SelectItem><SelectItem value="-updated_at">Recently updated</SelectItem></SelectContent></Select>
        </div>}
        actions={<><Button variant={view === "table" ? "secondary" : "ghost"} size="icon-sm" aria-label="Table view" onClick={() => { setView("table"); updatePreference("documentView", "table") }}><List /></Button><Button variant={view === "grid" ? "secondary" : "ghost"} size="icon-sm" aria-label="Grid view" onClick={() => { setView("grid"); updatePreference("documentView", "grid") }}><Grid2X2 /></Button></>}
      />
      {(searchInput || category) && <Button variant="ghost" size="sm" onClick={() => { setSearchInput(""); router.replace(APP_ROUTES.documents) }}>Clear filters</Button>}
      {documents.isLoading ? <TableSkeleton /> : documents.isError ? <ErrorState title="Documents could not be loaded" description="Check the connection and try again." action={<Button onClick={() => void documents.refetch()}>Retry</Button>} /> : rows.length === 0 ? <EmptyState title={filters.search || category ? "No matching documents" : "No documents available"} description={filters.search || category ? "Clear or adjust the current filters." : "Knowledge sources will appear here after they are added."} /> : view === "grid" ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{rows.map((document) => <button key={document.id} className="min-h-36 rounded-2xl border bg-card p-5 text-left shadow-sm transition duration-150 hover:-translate-y-0.5 hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transform-none motion-reduce:transition-none" onClick={() => setSelected(document)}><div className="flex items-start justify-between gap-3"><h2 className="min-w-0 break-words font-medium">{document.title}</h2><StatusBadge className="shrink-0">{document.category}</StatusBadge></div><p className="mt-4 text-sm text-muted-foreground">{document.author} · {document.extension?.replace(".", "").toUpperCase() ?? "Manual source"}</p><p className="mt-4 text-xs text-muted-foreground">Updated {formatDate(document.updated_at)}</p></button>)}</div>
      ) : (
        <ResponsiveDataTableContainer mobileFallback={rows.map((document) => <MobileCardFallback key={document.id} title={document.title} metadata={`${document.category} · ${formatDate(document.updated_at)}`} actions={<Button size="sm" variant="outline" onClick={() => setSelected(document)}>Details</Button>}><p className="break-all text-sm text-muted-foreground">{document.original_filename ?? document.author}</p></MobileCardFallback>)}>
          <Table><TableHeader><TableRow><TableHead>Document</TableHead><TableHead>Category</TableHead><TableHead>File</TableHead><TableHead>Updated</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader><TableBody>{rows.map((document) => <TableRow key={document.id}><TableCell><p className="font-medium">{document.title}</p><p className="text-xs text-muted-foreground">{document.author}</p></TableCell><TableCell><StatusBadge>{document.category}</StatusBadge></TableCell><TableCell>{document.extension?.replace(".", "").toUpperCase() ?? "Manual"}</TableCell><TableCell>{formatDate(document.updated_at)}</TableCell><TableCell className="text-right"><Button size="sm" variant="outline" onClick={() => setSelected(document)}>Details</Button></TableCell></TableRow>)}</TableBody></Table>
        </ResponsiveDataTableContainer>
      )}
      {rows.length > 0 && <PaginationControls page={page} pageCount={rows.length === limit ? page + 1 : page} onPrevious={() => updateParams({ page: page - 1 })} onNext={() => updateParams({ page: page + 1 })} />}

      <Sheet open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}><SheetContent className="w-full sm:max-w-lg"><SheetHeader className="border-b"><SheetTitle>{selected?.title}</SheetTitle></SheetHeader>{selected && <div className="flex-1 space-y-5 overflow-y-auto px-4"><div className="flex gap-2"><StatusBadge>{selected.category}</StatusBadge><StatusBadge tone={selected.is_active ? "success" : "neutral"}>{selected.is_active ? "Active" : "Inactive"}</StatusBadge></div><div><h3 className="text-sm font-medium">Stored content</h3><p className="mt-2 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-xl bg-muted/40 p-4 text-sm leading-6">{selected.content}</p></div><MetadataList items={[{ label: "File name", value: selected.original_filename ?? "Unavailable" },{ label: "MIME type", value: selected.mime_type ?? "Unavailable" },{ label: "File size", value: formatBytes(selected.file_size) },{ label: "Author", value: selected.author },{ label: "Created", value: formatDate(selected.created_at) },{ label: "Updated", value: formatDate(selected.updated_at) },{ label: "Uploaded", value: formatDate(selected.uploaded_at) },{ label: "Checksum", value: selected.checksum ? <span className="break-all">{selected.checksum}</span> : "Unavailable" },{ label: "Document ID", value: <span className="break-all">{selected.id}</span> }]} /></div>}<SheetFooter className="border-t">{selected && actions(selected)}</SheetFooter></SheetContent></Sheet>

      <Dialog open={editing !== null} onOpenChange={(open) => !open && setEditing(null)}><DialogContent><DialogHeader><DialogTitle>Edit document</DialogTitle><DialogDescription>Update supported catalog metadata. Changing content is intentionally excluded here.</DialogDescription></DialogHeader>{editing && <form onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); editMutation.mutate({ id: editing.id, title: String(data.get("title")), category: editCategory }) }}><FormSection title="Document metadata"><TextField label="Title" name="title" defaultValue={editing.title} required minLength={3} maxLength={150} /><SelectField label="Category" value={editCategory} onValueChange={(value) => setEditCategory(value as DocumentRecord["category"])} options={DOCUMENT_CATEGORIES.map((item) => ({ label: item, value: item }))} /><SubmitButton loading={editMutation.isPending}>Save changes</SubmitButton></FormSection></form>}</DialogContent></Dialog>
    </AppPageContainer>
  )
}

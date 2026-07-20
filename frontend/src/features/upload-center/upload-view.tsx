"use client"

import { useState } from "react"
import Link from "next/link"
import { useDropzone } from "react-dropzone"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Bot, CheckCircle2, FileText, RotateCcw, UploadCloud, X } from "lucide-react"
import { toast } from "sonner"

import { AppPageContainer } from "@/components/app-shell"
import { ErrorState, ProgressState } from "@/components/design-system/feedback"
import { FormSection, SelectField, SubmitButton, TextField } from "@/components/design-system/forms"
import { PageHeader } from "@/components/design-system/layout"
import { GlassPanel } from "@/components/design-system/surfaces"
import { Button } from "@/components/ui/button"
import { APP_ROUTES } from "@/constants"
import { useAuth } from "@/features/auth"
import { dashboardKeys } from "@/features/dashboard/api"
import { documentKeys, DOCUMENT_CATEGORIES, type DocumentRecord } from "@/features/documents"
import type { NormalizedApiError } from "@/lib/api/client"
import { cn } from "@/lib/utils"

import { uploadDocument } from "./api"

const MAX_SIZE = 5 * 1024 * 1024
const ACCEPT = {
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
}

export function UploadView() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState("")
  const [category, setCategory] = useState("HR")
  const [tags, setTags] = useState("")
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<DocumentRecord | null>(null)
  const dropzone = useDropzone({
    accept: ACCEPT,
    maxSize: MAX_SIZE,
    multiple: false,
    onDropAccepted: ([accepted]) => {
      if (accepted.size === 0) {
        setError("The selected file is empty.")
        return
      }
      setFile(accepted)
      setError(null)
      if (!title) setTitle(accepted.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " "))
    },
    onDropRejected: (rejections) => {
      const code = rejections[0]?.errors[0]?.code
      setError(code === "file-too-large" ? "Files must be 5 MB or smaller." : "Choose a TXT, Markdown, PDF, or DOCX file.")
    },
  })
  const mutation = useMutation<DocumentRecord, NormalizedApiError>({
    mutationFn: async () => {
      if (!file || !user) throw new Error("Missing upload information")
      const data = new FormData()
      data.append("file", file)
      data.append("category", category)
      if (title.trim()) data.append("title", title.trim())
      if (tags.trim()) data.append("tags", tags.trim())
      data.append("author", user.fullName)
      return uploadDocument(data, setProgress)
    },
    onSuccess: async (document) => {
      setCreated(document)
      toast.success("Document added to company knowledge.")
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentKeys.all }),
        queryClient.invalidateQueries({ queryKey: dashboardKeys.documents() }),
      ])
    },
    onError: (failure) => {
      setError(failure.message)
    },
  })

  function reset() {
    setFile(null); setTitle(""); setCategory("HR"); setTags(""); setProgress(0); setError(null); setCreated(null); mutation.reset()
  }

  if (created) {
    return (
      <AppPageContainer>
        <GlassPanel className="mx-auto max-w-2xl p-8 text-center">
          <CheckCircle2 className="mx-auto size-12 text-success" />
          <h1 className="mt-5 font-heading text-2xl font-semibold">Document uploaded successfully</h1>
          <p className="mt-2 text-muted-foreground">{created.title} is now available as an active knowledge source.</p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <Button nativeButton={false} render={<Link href={APP_ROUTES.documents} />}>View documents</Button>
            <Button nativeButton={false} variant="outline" render={<Link href={`${APP_ROUTES.chat}?prompt=${encodeURIComponent(`What should I know about "${created.title}"?`)}&category=${created.category}`} />}><Bot />Ask AI</Button>
            <Button variant="outline" onClick={reset}><RotateCcw />Upload another</Button>
          </div>
        </GlassPanel>
      </AppPageContainer>
    )
  }

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader eyebrow="Knowledge ingestion" title="Upload Documents" description="Add one supported document at a time. The request completes after extraction, chunking, and storage finish." />
      <form onSubmit={(event) => { event.preventDefault(); if (!file) setError("Select a file before uploading."); else if (title.trim() && title.trim().length < 3) setError("The title must contain at least 3 characters."); else mutation.mutate() }} className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <FormSection title="Select a document" description="TXT, Markdown, PDF, or DOCX. Maximum file size: 5 MB.">
          <div {...dropzone.getRootProps()} className={cn("flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50", dropzone.isDragActive ? "border-primary bg-primary/5" : "hover:border-primary/40 hover:bg-muted/30")}>
            <input {...dropzone.getInputProps()} aria-label="Choose a document to upload" />
            <UploadCloud className="size-10 text-primary" />
            <p className="mt-4 font-medium">{dropzone.isDragActive ? "Drop the document here" : "Drag and drop a document"}</p>
            <p className="mt-1 text-sm text-muted-foreground">or press Enter to browse files</p>
          </div>
          {file && <div className="flex items-center gap-3 rounded-xl border bg-muted/20 p-4"><FileText className="size-5 text-primary" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{file.name}</p><p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p></div><Button type="button" variant="ghost" size="icon" aria-label="Remove selected file" onClick={() => setFile(null)}><X /></Button></div>}
        </FormSection>
        <FormSection title="Document information">
          <TextField label="Title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={150} description="Optional. A title will be generated from the file name when blank." />
          <SelectField label="Category" required value={category} onValueChange={setCategory} options={DOCUMENT_CATEGORIES.map((item) => ({ label: item, value: item }))} />
          <TextField label="Tags" value={tags} onChange={(event) => setTags(event.target.value)} description="Optional comma-separated tags." />
          {mutation.isPending && <ProgressState label={progress < 100 ? "Uploading document" : "Processing document"} value={progress} detail={progress < 100 ? "Transferring the selected file." : "Extracting text, creating chunks, and finalizing the knowledge source. This stage is indeterminate."} />}
          {error && <ErrorState compact title={mutation.error?.status === 409 ? "Duplicate document" : "Upload needs attention"} description={error} />}
          <div className="flex gap-2"><SubmitButton loading={mutation.isPending} loadingLabel={progress < 100 ? "Uploading" : "Processing"}>Upload document</SubmitButton><Button type="button" variant="outline" disabled={mutation.isPending} onClick={reset}>Reset</Button></div>
        </FormSection>
      </form>
    </AppPageContainer>
  )
}

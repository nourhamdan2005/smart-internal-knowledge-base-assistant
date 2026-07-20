import { apiClient, normalizeApiError } from "@/lib/api/client"
import { siteConfig } from "@/config/site"
import { tokenStorage } from "@/features/auth/token-storage"

import type { QueryRequest, QueryResponse } from "./types"

interface BackendQueryResponse {
  answer: string
  sources: Array<{
    chunk_id: string
    chunk_index: number
    document_id: string
    title: string
    category: string
    excerpt: string
  }>
}

export interface ChatTransport {
  send(request: QueryRequest, signal?: AbortSignal): Promise<QueryResponse>
}

export interface StreamCallbacks {
  onStage(stage: string): void
  onDelta(text: string): void
  onSources(sources: SourceCitation[]): void
}

type SourceCitation = QueryResponse["sources"][number]

function mapSources(sources: BackendQueryResponse["sources"]): SourceCitation[] {
  return sources.map((source) => ({
    chunkId: source.chunk_id,
    chunkIndex: source.chunk_index,
    documentId: source.document_id,
    title: source.title,
    category: source.category,
    excerpt: source.excerpt,
  }))
}

export const fullResponseTransport: ChatTransport = {
  async send(request, signal) {
    try {
      const response = await apiClient.post<BackendQueryResponse>("/query/", request, {
        signal,
        timeout: 120_000,
      })
      if (typeof response.data.answer !== "string" || !Array.isArray(response.data.sources)) {
        throw new Error("Malformed query response")
      }
      return {
        answer: response.data.answer || "No answer was returned.",
        sources: mapSources(response.data.sources),
      }
    } catch (error) {
      throw normalizeApiError(error, "CGC Knowledge AI could not complete this request.")
    }
  },
}

export async function streamResponse(
  request: QueryRequest,
  callbacks: StreamCallbacks,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${siteConfig.apiUrl}/query/stream`, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(tokenStorage.get() ? { Authorization: `Bearer ${tokenStorage.get()}` } : {}),
    },
    body: JSON.stringify(request),
  })
  if (!response.ok || !response.body) {
    throw new Error(response.status === 404 ? "STREAMING_UNAVAILABLE" : "The answer stream could not start.")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let completed = false
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const blocks = buffer.split("\n\n")
    buffer = blocks.pop() ?? ""
    for (const block of blocks) {
      const event = block.match(/^event: (.+)$/m)?.[1]
      const raw = block.match(/^data: (.+)$/m)?.[1]
      if (!event || !raw) continue
      const data = JSON.parse(raw) as { stage?: string; text?: string; sources?: BackendQueryResponse["sources"]; message?: string }
      if (event === "status" && data.stage) callbacks.onStage(data.stage)
      if (event === "delta" && data.text) callbacks.onDelta(data.text)
      if (event === "sources" && data.sources) callbacks.onSources(mapSources(data.sources))
      if (event === "error") throw new Error(data.message ?? "The answer stream was interrupted.")
      if (event === "done") completed = true
    }
    if (done) break
  }
  if (!completed) throw new Error("The answer stream ended before completion.")
}

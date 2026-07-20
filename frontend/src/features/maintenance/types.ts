export interface HealthResponse {
  status: "ok" | "degraded" | "error"
  message: string
  qdrant?: "ready" | "unavailable" | "disabled" | string
}

export interface ChunkBackfillResult {
  total_documents: number
  processed_documents: number
  skipped_documents: number
  failed_documents: number
  created_chunks: number
  failures: Array<{ document_id: string; title: string; error: string }>
}

export interface EmbeddingBackfillResult {
  total_chunks: number
  processed_chunks: number
  skipped_chunks: number
  failed_chunks: number
  failures: Array<{
    chunk_id: string
    document_id: string
    document_title: string
    chunk_index: number
    error: string
  }>
}

export interface VectorBackfillResult {
  total_chunks: number
  eligible_chunks: number
  processed: number
  skipped: number
  failed: number
  batches: number
  collection: string
  errors: string[]
}

export type MaintenanceResult =
  | ChunkBackfillResult
  | EmbeddingBackfillResult
  | VectorBackfillResult

export type MaintenanceOperation = "chunks" | "embeddings" | "vectors"

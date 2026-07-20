export interface SourceCitation {
  chunkId: string
  chunkIndex: number
  documentId: string
  title: string
  category: string
  excerpt: string
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: string
  status: "complete" | "pending" | "error"
  sources?: SourceCitation[]
  durationMs?: number
}

export interface Conversation {
  id: string
  userId: string
  title: string
  createdAt: string
  updatedAt: string
  pinned: boolean
  category: string | null
  messages: ChatMessage[]
}

export interface QueryRequest {
  question: string
  category: string | null
}

export interface QueryResponse {
  answer: string
  sources: SourceCitation[]
}

export const DOCUMENT_CATEGORIES = [
  "HR", "IT", "Engineering", "API Docs", "Deployment",
  "Security", "Testing", "Onboarding", "Project Management",
] as const

export type DocumentCategory = (typeof DOCUMENT_CATEGORIES)[number]

export interface DocumentRecord {
  id: string
  title: string
  category: DocumentCategory
  content: string
  tags: string[]
  author: string
  is_active: boolean
  created_at: string
  updated_at: string
  original_filename: string | null
  extension: string | null
  mime_type: string | null
  file_size: number | null
  checksum: string | null
  uploaded_at: string | null
}

export interface DocumentFilters {
  search: string
  category: string
  sort: string
  page: number
  limit: number
}

export interface DocumentUpdate {
  title?: string
  category?: DocumentCategory
  is_active?: boolean
}

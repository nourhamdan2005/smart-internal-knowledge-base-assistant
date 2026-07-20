import { apiClient, normalizeApiError } from "@/lib/api/client"

import type { DocumentFilters, DocumentRecord, DocumentUpdate } from "./types"

export const documentKeys = {
  all: ["documents"] as const,
  lists: () => [...documentKeys.all, "list"] as const,
  list: (filters: DocumentFilters) => [...documentKeys.lists(), filters] as const,
  detail: (id: string) => [...documentKeys.all, "detail", id] as const,
}

export async function listDocuments(filters: DocumentFilters, signal?: AbortSignal) {
  try {
    const response = await apiClient.get<DocumentRecord[]>("/documents", {
      params: {
        search: filters.search || undefined,
        category: filters.category || undefined,
        sort: filters.sort,
        page: filters.page,
        limit: filters.limit,
      },
      signal,
    })
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "Documents could not be loaded.")
  }
}

export async function updateDocument(id: string, update: DocumentUpdate) {
  try {
    const response = await apiClient.patch<DocumentRecord>(`/documents/${id}`, update)
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "The document could not be updated.")
  }
}

export async function deleteDocument(id: string) {
  try {
    await apiClient.delete(`/documents/${id}`)
  } catch (error) {
    throw normalizeApiError(error, "The document could not be deleted.")
  }
}

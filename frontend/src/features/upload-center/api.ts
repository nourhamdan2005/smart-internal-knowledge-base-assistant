import { apiClient, normalizeApiError } from "@/lib/api/client"
import type { DocumentRecord } from "@/features/documents"

export async function uploadDocument(
  data: FormData,
  onProgress: (percent: number) => void,
) {
  try {
    const response = await apiClient.post<DocumentRecord>("/uploads/", data, {
      timeout: 120_000,
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (event) => {
        if (event.total) onProgress(Math.round((event.loaded / event.total) * 100))
      },
    })
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "The document could not be uploaded.")
  }
}

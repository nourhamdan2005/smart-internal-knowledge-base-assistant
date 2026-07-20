import { apiClient } from "@/lib/api/client"

import type { DashboardDocument, DashboardUser, HealthResponse } from "./types"

export const dashboardKeys = {
  all: ["dashboard"] as const,
  documents: () => [...dashboardKeys.all, "documents"] as const,
  users: () => [...dashboardKeys.all, "users"] as const,
  health: () => [...dashboardKeys.all, "health"] as const,
}

export async function getDashboardDocuments(signal?: AbortSignal) {
  const response = await apiClient.get<DashboardDocument[]>("/documents", {
    params: { limit: 100, sort: "-created_at" },
    signal,
  })
  return response.data
}

export async function getDashboardUsers(signal?: AbortSignal) {
  const response = await apiClient.get<DashboardUser[]>("/users", {
    params: { limit: 100 },
    signal,
  })
  return response.data
}

export async function getReadiness(signal?: AbortSignal) {
  const response = await apiClient.get<HealthResponse>("/ready", {
    signal,
    validateStatus: (status) => status === 200 || status === 503,
  })
  return response.data
}

import { apiClient, normalizeApiError } from "@/lib/api/client"

import type {
  HealthResponse,
  MaintenanceOperation,
  MaintenanceResult,
} from "./types"

export const maintenanceKeys = {
  all: ["maintenance"] as const,
  health: () => [...maintenanceKeys.all, "health"] as const,
  readiness: () => [...maintenanceKeys.all, "readiness"] as const,
}

export async function getHealth(signal?: AbortSignal) {
  try {
    const response = await apiClient.get<HealthResponse>("/health", { signal })
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "Service health could not be loaded.")
  }
}

export async function getReadiness(signal?: AbortSignal) {
  try {
    const response = await apiClient.get<HealthResponse>("/ready", {
      signal,
      validateStatus: (status) => status === 200 || status === 503,
    })
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "Service readiness could not be loaded.")
  }
}

export async function runMaintenance(operation: MaintenanceOperation) {
  try {
    const response = await apiClient.post<MaintenanceResult>(
      `/maintenance/backfill-${operation}`,
      undefined,
      { timeout: 300_000 },
    )
    return response.data
  } catch (error) {
    throw normalizeApiError(error, `The ${operation} backfill failed.`)
  }
}

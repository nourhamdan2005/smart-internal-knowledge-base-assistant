import { apiClient, normalizeApiError } from "@/lib/api/client"

import type { CreateUserInput, ManagedUser, UpdateUserInput } from "./types"

export const userKeys = {
  all: ["users"] as const,
  list: () => [...userKeys.all, "list"] as const,
  detail: (id: string) => [...userKeys.all, "detail", id] as const,
}

export async function listManagedUsers(signal?: AbortSignal) {
  try {
    const response = await apiClient.get<ManagedUser[]>("/users", { params: { limit: 100 }, signal })
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "Users could not be loaded.")
  }
}

export async function createManagedUser(input: CreateUserInput) {
  try {
    const response = await apiClient.post<ManagedUser>("/users", input)
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "The user could not be created.")
  }
}

export async function updateManagedUser(id: string, input: UpdateUserInput) {
  try {
    const response = await apiClient.patch<ManagedUser>(`/users/${id}`, input)
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "The user could not be updated.")
  }
}

export async function deactivateManagedUser(id: string) {
  try {
    await apiClient.delete(`/users/${id}`)
  } catch (error) {
    throw normalizeApiError(error, "The user could not be deactivated.")
  }
}

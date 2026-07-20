import { apiClient, normalizeApiError } from "@/lib/api/client"

import type {
  AuthenticatedUser,
  LoginCredentials,
  LoginResponse,
} from "./types"

interface CurrentUserResponse {
  id: string
  email: string
  full_name: string
  role: AuthenticatedUser["role"]
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export async function loginRequest(
  credentials: Omit<LoginCredentials, "rememberMe">,
): Promise<LoginResponse> {
  try {
    const response = await apiClient.post<LoginResponse>("/auth/login", credentials)
    return response.data
  } catch (error) {
    throw normalizeApiError(error, "Unable to sign in right now.")
  }
}

export async function getCurrentUser(
  signal?: AbortSignal,
): Promise<AuthenticatedUser> {
  try {
    const response = await apiClient.get<CurrentUserResponse>("/auth/me", { signal })
    const user = response.data
    return {
      id: user.id,
      email: user.email,
      fullName: user.full_name,
      role: user.role,
      isActive: user.is_active,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
      lastLoginAt: user.last_login_at,
    }
  } catch (error) {
    throw normalizeApiError(error, "Unable to verify your session.")
  }
}

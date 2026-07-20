import type { UserRole } from "@/constants"

export interface LoginCredentials {
  email: string
  password: string
  rememberMe: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthenticatedUser {
  id: string
  email: string
  fullName: string
  role: UserRole
  isActive: boolean
  createdAt: string
  updatedAt: string
  lastLoginAt: string | null
  avatarUrl?: string
}

export type AuthStatus =
  | "initializing"
  | "authenticated"
  | "unauthenticated"
  | "unavailable"

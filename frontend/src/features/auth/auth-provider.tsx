"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import type { Permission } from "@/constants"
import { hasAnyPermission, hasEveryPermission, hasPermission } from "@/utils"
import { chatHistoryStorage } from "@/features/ai-chat/storage"
import type { NormalizedApiError } from "@/lib/api/client"

import { getCurrentUser, loginRequest } from "./api"
import { tokenStorage } from "./token-storage"
import type { AuthenticatedUser, AuthStatus, LoginCredentials } from "./types"

interface AuthContextValue {
  user: AuthenticatedUser | null
  role: AuthenticatedUser["role"] | null
  status: AuthStatus
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshCurrentUser: () => Promise<void>
  hasPermission: (permission: Permission) => boolean
  hasAnyPermission: (permissions: readonly Permission[]) => boolean
  hasEveryPermission: (permissions: readonly Permission[]) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [status, setStatus] = useState<AuthStatus>("initializing")

  const refreshCurrentUser = useCallback(async () => {
    if (!tokenStorage.get()) {
      setUser(null)
      setStatus("unauthenticated")
      return
    }
    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      setStatus("authenticated")
    } catch (error) {
      const normalized = error as NormalizedApiError
      if (normalized.kind === "authentication") {
        tokenStorage.clear()
        setUser(null)
        setStatus("unauthenticated")
      } else {
        setStatus("unavailable")
      }
    }
  }, [])

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      void refreshCurrentUser()
    })
    return () => window.cancelAnimationFrame(frame)
  }, [refreshCurrentUser])

  useEffect(() => {
    const handleUnauthorized = () => {
      tokenStorage.clear()
      setUser(null)
      setStatus("unauthenticated")
      toast.warning("Your session has expired. Please sign in again.")
    }
    window.addEventListener("auth:unauthorized", handleUnauthorized)
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized)
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const result = await loginRequest(credentials)
    tokenStorage.set(result.access_token, credentials.rememberMe)
    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      setStatus("authenticated")
    } catch (error) {
      tokenStorage.clear()
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    if (user) chatHistoryStorage.clear(user.id)
    tokenStorage.clear()
    setUser(null)
    setStatus("unauthenticated")
    queryClient.clear()
  }, [queryClient, user])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    role: user?.role ?? null,
    status,
    isAuthenticated: status === "authenticated",
    isLoading: status === "initializing",
    login,
    logout,
    refreshCurrentUser,
    hasPermission: (permission) => user ? hasPermission(user.role, permission) : false,
    hasAnyPermission: (permissions) => user ? hasAnyPermission(user.role, permissions) : false,
    hasEveryPermission: (permissions) => user ? hasEveryPermission(user.role, permissions) : false,
  }), [login, logout, refreshCurrentUser, status, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within AuthProvider")
  return context
}

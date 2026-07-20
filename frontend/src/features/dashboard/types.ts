import type { UserRole } from "@/constants"

export interface DashboardDocument {
  id: string
  title: string
  category: string
  author: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DashboardUser {
  id: string
  role: UserRole
  is_active: boolean
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error"
  message: string
  qdrant?: string
}

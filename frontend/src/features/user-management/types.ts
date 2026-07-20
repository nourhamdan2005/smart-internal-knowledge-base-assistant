import type { UserRole } from "@/constants"

export interface ManagedUser {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export interface CreateUserInput {
  email: string
  full_name: string
  password: string
  role: UserRole
}

export interface UpdateUserInput {
  email?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

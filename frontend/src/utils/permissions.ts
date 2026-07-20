import {
  ROLE_PERMISSIONS,
  type Permission,
  type UserRole,
} from "@/constants/permissions"

export function hasPermission(
  role: UserRole,
  permission: Permission,
): boolean {
  const permissions: readonly Permission[] = ROLE_PERMISSIONS[role]
  return permissions.includes(permission)
}

export function hasEveryPermission(
  role: UserRole,
  permissions: readonly Permission[],
): boolean {
  return permissions.every((permission) => hasPermission(role, permission))
}

export function hasAnyPermission(
  role: UserRole,
  permissions: readonly Permission[],
): boolean {
  return permissions.some((permission) => hasPermission(role, permission))
}

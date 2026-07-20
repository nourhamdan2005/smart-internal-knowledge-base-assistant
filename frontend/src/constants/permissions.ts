export const USER_ROLES = {
  admin: "admin",
  editor: "editor",
  employee: "employee",
} as const

export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES]

export const PERMISSIONS = {
  dashboardView: "dashboard:view",
  chatQuery: "chat:query",
  documentsView: "documents:view",
  documentsCreate: "documents:create",
  documentsUpdate: "documents:update",
  documentsDelete: "documents:delete",
  uploadsView: "uploads:view",
  uploadsCreate: "uploads:create",
  usersView: "users:view",
  usersManage: "users:manage",
  maintenanceView: "maintenance:view",
  maintenanceManage: "maintenance:manage",
  systemHealthView: "system-health:view",
  profileView: "profile:view",
  settingsView: "settings:view",
} as const

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

const employeePermissions = [
  PERMISSIONS.dashboardView,
  PERMISSIONS.chatQuery,
  PERMISSIONS.documentsView,
  PERMISSIONS.profileView,
  PERMISSIONS.settingsView,
] as const satisfies readonly Permission[]

const editorPermissions = [
  ...employeePermissions,
  PERMISSIONS.documentsCreate,
  PERMISSIONS.documentsUpdate,
  PERMISSIONS.uploadsView,
  PERMISSIONS.uploadsCreate,
] as const satisfies readonly Permission[]

export const ROLE_PERMISSIONS = {
  [USER_ROLES.admin]: Object.values(PERMISSIONS),
  [USER_ROLES.editor]: editorPermissions,
  [USER_ROLES.employee]: employeePermissions,
} as const satisfies Record<UserRole, readonly Permission[]>

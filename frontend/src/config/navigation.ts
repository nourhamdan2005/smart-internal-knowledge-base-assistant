import type { LucideIcon } from "lucide-react"
import {
  Activity,
  Bot,
  Gauge,
  HardDriveUpload,
  Library,
  Settings,
  UserRound,
  Users,
  Wrench,
} from "lucide-react"

import {
  APP_ROUTES,
  PERMISSIONS,
  type AppRoute,
  type Permission,
  type UserRole,
} from "@/constants"
import { hasPermission } from "@/utils"

export type NavigationSectionId = "workspace" | "administration" | "account"

export interface NavigationItem {
  label: string
  href: AppRoute
  icon: LucideIcon
  permission: Permission
  section: NavigationSectionId
  badge?: string
  exact?: boolean
}

export const NAVIGATION_SECTIONS: ReadonlyArray<{
  id: NavigationSectionId
  label: string
}> = [
  { id: "workspace", label: "Workspace" },
  { id: "administration", label: "Administration" },
  { id: "account", label: "Account" },
]

export const NAVIGATION_ITEMS: readonly NavigationItem[] = [
  {
    label: "Dashboard",
    href: APP_ROUTES.dashboard,
    icon: Gauge,
    permission: PERMISSIONS.dashboardView,
    section: "workspace",
    exact: true,
  },
  {
    label: "AI Chat",
    href: APP_ROUTES.chat,
    icon: Bot,
    permission: PERMISSIONS.chatQuery,
    section: "workspace",
  },
  {
    label: "Documents",
    href: APP_ROUTES.documents,
    icon: Library,
    permission: PERMISSIONS.documentsView,
    section: "workspace",
  },
  {
    label: "Upload Documents",
    href: APP_ROUTES.uploadCenter,
    icon: HardDriveUpload,
    permission: PERMISSIONS.uploadsView,
    section: "workspace",
  },
  {
    label: "User Management",
    href: APP_ROUTES.users,
    icon: Users,
    permission: PERMISSIONS.usersView,
    section: "administration",
  },
  {
    label: "Maintenance",
    href: APP_ROUTES.maintenance,
    icon: Wrench,
    permission: PERMISSIONS.maintenanceView,
    section: "administration",
  },
  {
    label: "System Health",
    href: APP_ROUTES.systemHealth,
    icon: Activity,
    permission: PERMISSIONS.systemHealthView,
    section: "administration",
  },
  {
    label: "Profile",
    href: APP_ROUTES.profile,
    icon: UserRound,
    permission: PERMISSIONS.profileView,
    section: "account",
  },
  {
    label: "Settings",
    href: APP_ROUTES.settings,
    icon: Settings,
    permission: PERMISSIONS.settingsView,
    section: "account",
  },
] as const

export function getNavigationForRole(role: UserRole): NavigationItem[] {
  return NAVIGATION_ITEMS.filter((item) => hasPermission(role, item.permission))
}

export function isNavigationItemActive(
  pathname: string,
  item: Pick<NavigationItem, "href" | "exact">,
): boolean {
  return item.exact
    ? pathname === item.href
    : pathname === item.href || pathname.startsWith(`${item.href}/`)
}

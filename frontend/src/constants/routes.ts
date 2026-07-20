export const APP_ROUTES = {
  home: "/",
  login: "/login",
  dashboard: "/dashboard",
  chat: "/chat",
  documents: "/documents",
  uploadCenter: "/uploads",
  users: "/users",
  maintenance: "/maintenance",
  systemHealth: "/system-health",
  profile: "/profile",
  settings: "/settings",
  designSystem: "/design-system",
} as const

export type AppRoute = (typeof APP_ROUTES)[keyof typeof APP_ROUTES]

export const PUBLIC_ROUTES = [
  APP_ROUTES.home,
  APP_ROUTES.login,
] as const satisfies readonly AppRoute[]

export const INTERNAL_ROUTES = [
  APP_ROUTES.designSystem,
] as const satisfies readonly AppRoute[]

export const ROUTE_METADATA = {
  [APP_ROUTES.home]: { label: "Home" },
  [APP_ROUTES.login]: { label: "Sign in" },
  [APP_ROUTES.dashboard]: { label: "Dashboard" },
  [APP_ROUTES.chat]: { label: "AI Chat" },
  [APP_ROUTES.documents]: { label: "Documents" },
  [APP_ROUTES.uploadCenter]: { label: "Upload Documents" },
  [APP_ROUTES.users]: { label: "User Management" },
  [APP_ROUTES.maintenance]: { label: "Maintenance" },
  [APP_ROUTES.systemHealth]: { label: "System Health" },
  [APP_ROUTES.profile]: { label: "Profile" },
  [APP_ROUTES.settings]: { label: "Settings" },
  [APP_ROUTES.designSystem]: { label: "Design System" },
} as const satisfies Record<AppRoute, { label: string }>

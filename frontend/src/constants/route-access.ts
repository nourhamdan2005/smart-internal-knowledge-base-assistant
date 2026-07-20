import { APP_ROUTES, type AppRoute } from "./routes"
import { PERMISSIONS, type Permission } from "./permissions"

export const ROUTE_ACCESS = {
  [APP_ROUTES.dashboard]: PERMISSIONS.dashboardView,
  [APP_ROUTES.chat]: PERMISSIONS.chatQuery,
  [APP_ROUTES.documents]: PERMISSIONS.documentsView,
  [APP_ROUTES.uploadCenter]: PERMISSIONS.uploadsView,
  [APP_ROUTES.users]: PERMISSIONS.usersView,
  [APP_ROUTES.maintenance]: PERMISSIONS.maintenanceView,
  [APP_ROUTES.systemHealth]: PERMISSIONS.systemHealthView,
  [APP_ROUTES.profile]: PERMISSIONS.profileView,
  [APP_ROUTES.settings]: PERMISSIONS.settingsView,
} as const satisfies Partial<Record<AppRoute, Permission>>

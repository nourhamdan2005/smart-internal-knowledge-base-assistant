export type MotionPreference = "system" | "reduced" | "standard"
export type DocumentViewPreference = "table" | "grid"
export type ChatDensityPreference = "comfortable" | "compact"

export interface AppPreferences {
  motion: MotionPreference
  sidebarExpanded: boolean
  documentView: DocumentViewPreference
  pageSize: 10 | 20 | 50
  chatDensity: ChatDensityPreference
  chatSourcesOpen: boolean
}

export const DEFAULT_PREFERENCES: AppPreferences = {
  motion: "system",
  sidebarExpanded: true,
  documentView: "table",
  pageSize: 10,
  chatDensity: "comfortable",
  chatSourcesOpen: false,
}

import { STORAGE_KEYS } from "@/constants"

import { DEFAULT_PREFERENCES, type AppPreferences } from "./types"

const VERSION = 1

interface StoredPreferences {
  version: number
  preferences: AppPreferences
}

function isPreferences(value: unknown): value is AppPreferences {
  if (!value || typeof value !== "object") return false
  const item = value as Partial<AppPreferences>
  return (
    ["system", "reduced", "standard"].includes(item.motion ?? "") &&
    typeof item.sidebarExpanded === "boolean" &&
    ["table", "grid"].includes(item.documentView ?? "") &&
    [10, 20, 50].includes(item.pageSize ?? 0) &&
    ["comfortable", "compact"].includes(item.chatDensity ?? "") &&
    typeof item.chatSourcesOpen === "boolean"
  )
}

export const preferencesStorage = {
  load(): AppPreferences {
    if (typeof window === "undefined") return DEFAULT_PREFERENCES
    try {
      const parsed = JSON.parse(
        window.localStorage.getItem(STORAGE_KEYS.preferences) ?? "",
      ) as StoredPreferences
      return parsed.version === VERSION && isPreferences(parsed.preferences)
        ? parsed.preferences
        : DEFAULT_PREFERENCES
    } catch {
      return DEFAULT_PREFERENCES
    }
  },
  save(preferences: AppPreferences) {
    window.localStorage.setItem(
      STORAGE_KEYS.preferences,
      JSON.stringify({ version: VERSION, preferences }),
    )
  },
  clear() {
    window.localStorage.removeItem(STORAGE_KEYS.preferences)
  },
}

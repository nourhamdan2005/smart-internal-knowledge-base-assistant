"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"

import { preferencesStorage } from "./storage"
import { DEFAULT_PREFERENCES, type AppPreferences } from "./types"

interface PreferencesContextValue {
  preferences: AppPreferences
  hydrated: boolean
  updatePreference: <Key extends keyof AppPreferences>(
    key: Key,
    value: AppPreferences[Key],
  ) => void
  resetPreferences: () => void
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null)

export function PreferencesProvider({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setPreferences(preferencesStorage.load())
      setHydrated(true)
    })
    return () => window.cancelAnimationFrame(frame)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    preferencesStorage.save(preferences)
    document.documentElement.dataset.motion = preferences.motion
  }, [hydrated, preferences])

  const updatePreference = useCallback(
    <Key extends keyof AppPreferences>(
      key: Key,
      value: AppPreferences[Key],
    ) => setPreferences((current) => ({ ...current, [key]: value })),
    [],
  )
  const resetPreferences = useCallback(() => {
    preferencesStorage.clear()
    setPreferences(DEFAULT_PREFERENCES)
  }, [])

  const value = useMemo(
    () => ({ preferences, hydrated, updatePreference, resetPreferences }),
    [hydrated, preferences, resetPreferences, updatePreference],
  )

  return (
    <PreferencesContext.Provider value={value}>
      {children}
    </PreferencesContext.Provider>
  )
}

export function usePreferences() {
  const context = useContext(PreferencesContext)
  if (!context) {
    throw new Error("usePreferences must be used within PreferencesProvider")
  }
  return context
}

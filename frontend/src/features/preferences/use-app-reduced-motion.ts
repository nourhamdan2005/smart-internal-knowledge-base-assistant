"use client"

import { useReducedMotion } from "motion/react"

import { usePreferences } from "./preferences-provider"

export function useAppReducedMotion() {
  const systemReduced = useReducedMotion()
  const { preferences } = usePreferences()
  if (preferences.motion === "reduced") return true
  if (preferences.motion === "standard") return false
  return Boolean(systemReduced)
}

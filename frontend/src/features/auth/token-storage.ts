import { STORAGE_KEYS } from "@/constants/storage"

// Temporary browser-token storage until the backend supports HTTP-only cookies.
export const tokenStorage = {
  get(): string | null {
    if (typeof window === "undefined") return null
    return (
      window.sessionStorage.getItem(STORAGE_KEYS.accessToken) ??
      window.localStorage.getItem(STORAGE_KEYS.accessToken)
    )
  },
  set(token: string, remember: boolean) {
    if (typeof window === "undefined") return
    this.clear()
    const storage = remember ? window.localStorage : window.sessionStorage
    storage.setItem(STORAGE_KEYS.accessToken, token)
  },
  clear() {
    if (typeof window === "undefined") return
    window.localStorage.removeItem(STORAGE_KEYS.accessToken)
    window.sessionStorage.removeItem(STORAGE_KEYS.accessToken)
  },
}

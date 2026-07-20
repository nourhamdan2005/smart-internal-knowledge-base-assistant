"use client"

import { useEffect, useState } from "react"
import { WifiOff } from "lucide-react"

export function OfflineBanner() {
  const [online, setOnline] = useState(true)

  useEffect(() => {
    const update = () => setOnline(window.navigator.onLine)
    update()
    window.addEventListener("online", update)
    window.addEventListener("offline", update)
    return () => {
      window.removeEventListener("online", update)
      window.removeEventListener("offline", update)
    }
  }, [])

  if (online) return null
  return (
    <div role="status" className="flex items-center justify-center gap-2 border-b border-warning/25 bg-warning/10 px-4 py-2 text-center text-xs font-medium text-warning">
      <WifiOff className="size-3.5" aria-hidden="true" />
      You are offline. Local preferences and saved chat history remain available; server actions will resume after reconnection.
    </div>
  )
}

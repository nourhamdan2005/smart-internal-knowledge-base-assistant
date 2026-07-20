import { STORAGE_KEYS } from "@/constants/storage"

import type { Conversation } from "./types"

const VERSION = 1
const MAX_CONVERSATIONS = 50

interface StoredHistory {
  version: number
  conversations: Conversation[]
}

function key(userId: string) {
  return `${STORAGE_KEYS.chatHistoryPrefix}:${userId}`
}

export const chatHistoryStorage = {
  load(userId: string): Conversation[] {
    if (typeof window === "undefined") return []
    try {
      const parsed = JSON.parse(window.localStorage.getItem(key(userId)) ?? "") as StoredHistory
      if (parsed.version !== VERSION || !Array.isArray(parsed.conversations)) return []
      return parsed.conversations.filter((conversation) => conversation.userId === userId)
    } catch {
      return []
    }
  },
  save(userId: string, conversations: Conversation[]) {
    if (typeof window === "undefined") return
    const retained = [...conversations]
      .sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.updatedAt.localeCompare(a.updatedAt))
      .slice(0, MAX_CONVERSATIONS)
    window.localStorage.setItem(key(userId), JSON.stringify({ version: VERSION, conversations: retained }))
  },
  clear(userId: string) {
    if (typeof window === "undefined") return
    window.localStorage.removeItem(key(userId))
  },
}

export function groupConversations(conversations: Conversation[]) {
  const groups: Record<"Today" | "Yesterday" | "Previous 7 Days" | "Older", Conversation[]> = {
    Today: [], Yesterday: [], "Previous 7 Days": [], Older: [],
  }
  const now = new Date()
  for (const conversation of conversations) {
    const date = new Date(conversation.updatedAt)
    const days = Math.floor((new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() - new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()) / 86_400_000)
    groups[days <= 0 ? "Today" : days === 1 ? "Yesterday" : days <= 7 ? "Previous 7 Days" : "Older"].push(conversation)
  }
  return groups
}

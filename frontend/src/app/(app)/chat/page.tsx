import { Suspense } from "react"

import { LoadingState } from "@/components/design-system/feedback"
import { ChatView } from "@/features/ai-chat"

export default function ChatPage() {
  return <Suspense fallback={<LoadingState fullPage label="Opening conversation" />}><ChatView /></Suspense>
}

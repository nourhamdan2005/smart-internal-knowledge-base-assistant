import { Suspense } from "react"

import { LoadingState } from "@/components/design-system/feedback"
import { DocumentsView } from "@/features/documents"

export default function DocumentsPage() {
  return <Suspense fallback={<LoadingState fullPage label="Loading documents" />}><DocumentsView /></Suspense>
}

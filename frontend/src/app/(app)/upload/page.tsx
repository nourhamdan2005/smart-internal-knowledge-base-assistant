import { redirect } from "next/navigation"

import { APP_ROUTES } from "@/constants"

export default function UploadAliasPage() {
  redirect(APP_ROUTES.uploadCenter)
}

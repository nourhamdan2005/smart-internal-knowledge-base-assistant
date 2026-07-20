"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { APP_ROUTES, ROUTE_METADATA, type AppRoute } from "@/constants/routes"

function labelForPath(path: string) {
  const metadata = ROUTE_METADATA[path as AppRoute]
  if (metadata) return metadata.label

  return path
    .split("/")
    .filter(Boolean)
    .at(-1)
    ?.replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase()) ?? "Page"
}

export function AppBreadcrumbs() {
  const pathname = usePathname()
  const isDashboard = pathname === APP_ROUTES.dashboard

  return (
    <Breadcrumb className="min-w-0">
      <BreadcrumbList className="flex-nowrap">
        <BreadcrumbItem className="min-w-0">
          {isDashboard ? (
            <BreadcrumbPage className="truncate">Dashboard</BreadcrumbPage>
          ) : (
            <BreadcrumbLink
              render={<Link href={APP_ROUTES.dashboard} />}
              className="truncate"
            >
              Dashboard
            </BreadcrumbLink>
          )}
        </BreadcrumbItem>
        {!isDashboard && (
          <>
            <BreadcrumbSeparator />
            <BreadcrumbItem className="min-w-0">
              <BreadcrumbPage className="max-w-48 truncate sm:max-w-72">
                {labelForPath(pathname)}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </>
        )}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

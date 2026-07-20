"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { BrandMark } from "@/components/design-system/brand"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import {
  getNavigationForRole,
  isNavigationItemActive,
  NAVIGATION_SECTIONS,
} from "@/config/navigation"
import { siteConfig } from "@/config/site"
import { APP_ROUTES } from "@/constants/routes"
import type { AuthenticatedUser } from "@/features/auth"

import { UserIdentity } from "./user-identity"

export function AppSidebar({
  session,
}: Readonly<{ session: AuthenticatedUser }>) {
  const pathname = usePathname()
  const { setOpenMobile } = useSidebar()
  const navigation = getNavigationForRole(session.role)

  return (
    <Sidebar collapsible="icon" aria-label="Application navigation">
      <SidebarHeader className="border-b border-sidebar-border p-3">
        <Link
          href={APP_ROUTES.dashboard}
          className="flex h-10 items-center gap-3 overflow-hidden rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
          aria-label={`${siteConfig.name} dashboard`}
          onClick={() => setOpenMobile(false)}
        >
          <BrandMark className="size-9 rounded-lg group-data-[collapsible=icon]:size-8" />
          <span className="min-w-0 group-data-[collapsible=icon]:hidden">
            <span className="block truncate font-heading text-sm font-semibold">
              {siteConfig.name}
            </span>
            <span className="block truncate text-[0.68rem] text-sidebar-foreground/60">
              Enterprise knowledge intelligence
            </span>
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent className="py-3">
        {NAVIGATION_SECTIONS.map((section) => {
          const items = navigation.filter((item) => item.section === section.id)
          if (items.length === 0) return null

          return (
            <SidebarGroup key={section.id} className="py-1.5">
              <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {items.map((item) => {
                    const active = isNavigationItemActive(pathname, item)
                    const Icon = item.icon

                    return (
                      <SidebarMenuItem key={item.href}>
                        <SidebarMenuButton
                          render={<Link href={item.href} />}
                          isActive={active}
                          tooltip={item.label}
                          aria-current={active ? "page" : undefined}
                          onClick={() => setOpenMobile(false)}
                          className="h-9 data-active:bg-primary/10 data-active:text-primary data-active:ring-1 data-active:ring-primary/15"
                        >
                          <Icon aria-hidden="true" />
                          <span>{item.label}</span>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    )
                  })}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          )
        })}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-3">
        <UserIdentity
          user={session}
          showRole
          className="rounded-lg p-1 group-data-[collapsible=icon]:[&>div]:hidden"
        />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

"use client"

import { LogOut, Settings, UserRound } from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { APP_ROUTES } from "@/constants/routes"
import { useAuth, type AuthenticatedUser } from "@/features/auth"

import { UserIdentity } from "./user-identity"

export function AppUserMenu({
  session,
}: Readonly<{ session: AuthenticatedUser }>) {
  const { logout } = useAuth()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            className="h-9 gap-2 rounded-full px-1.5 sm:pr-3"
            aria-label="Open user menu"
          />
        }
      >
        <UserIdentity user={session} compact className="[&>div]:hidden" />
        <span className="hidden max-w-40 truncate text-sm lg:inline" title={session.fullName}>
          {session.fullName}
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="p-2">
            <UserIdentity user={session} showRole />
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href={APP_ROUTES.profile} />}>
          <UserRound /> Profile
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href={APP_ROUTES.settings} />}>
          <Settings /> Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => {
            logout()
            toast.success("You have been signed out.")
            window.location.assign(APP_ROUTES.login)
          }}
        >
          <LogOut /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

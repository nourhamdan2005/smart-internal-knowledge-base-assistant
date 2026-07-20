import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { RoleBadge } from "@/components/design-system/status"
import type { AuthenticatedUser } from "@/features/auth"
import { cn } from "@/lib/utils"

export function getUserInitials(fullName: string) {
  return fullName
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase()
}

export function UserIdentity({
  user,
  compact = false,
  showRole = false,
  className,
}: Readonly<{
  user: AuthenticatedUser
  compact?: boolean
  showRole?: boolean
  className?: string
}>) {
  return (
    <div className={cn("flex min-w-0 items-center gap-3", className)}>
      <Avatar size={compact ? "sm" : "default"}>
        {user.avatarUrl && <AvatarImage src={user.avatarUrl} alt="" />}
        <AvatarFallback>{getUserInitials(user.fullName)}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium" title={user.fullName}>
          {user.fullName}
        </p>
        {showRole ? (
          <div className="mt-1"><RoleBadge role={user.role} /></div>
        ) : (
          <p className="truncate text-xs text-muted-foreground" title={user.email}>
            {user.email}
          </p>
        )}
      </div>
    </div>
  )
}

import { cva, type VariantProps } from "class-variance-authority"

import { Badge } from "@/components/ui/badge"
import type { UserRole } from "@/constants/permissions"
import { cn } from "@/lib/utils"

const statusStyles = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-border bg-muted/70 text-muted-foreground",
        success:
          "border-success/20 bg-success/10 text-success",
        warning:
          "border-warning/20 bg-warning/10 text-warning",
        danger:
          "border-destructive/20 bg-destructive/10 text-destructive",
        info: "border-primary/20 bg-primary/10 text-primary",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
)

export function StatusBadge({
  tone,
  className,
  children,
}: React.ComponentProps<"span"> &
  VariantProps<typeof statusStyles>) {
  return (
    <span className={cn(statusStyles({ tone }), className)}>
      {children}
    </span>
  )
}

export function RoleBadge({
  role,
}: Readonly<{ role: UserRole }>) {
  const styles = {
    admin: "border-violet-500/20 bg-violet-500/10 text-violet-700 dark:text-violet-300",
    editor: "border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-300",
    employee: "border-border bg-muted text-muted-foreground",
  }

  return (
    <Badge variant="outline" className={styles[role]}>
      {role.charAt(0).toUpperCase() + role.slice(1)}
    </Badge>
  )
}

export function HealthIndicator({
  status,
  label,
}: Readonly<{
  status: "healthy" | "degraded" | "offline" | "disabled"
  label: string
}>) {
  const colors = {
    healthy: "bg-success",
    degraded: "bg-warning",
    offline: "bg-destructive",
    disabled: "bg-muted-foreground",
  }

  return (
    <span className="inline-flex items-center gap-2 text-sm">
      <span className="relative flex size-2.5" aria-hidden="true">
        {status === "healthy" && (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-success opacity-50 motion-reduce:animate-none" />
        )}
        <span className={cn("relative inline-flex size-2.5 rounded-full", colors[status])} />
      </span>
      <span>{label}</span>
      <span className="sr-only">Status: {status}</span>
    </span>
  )
}

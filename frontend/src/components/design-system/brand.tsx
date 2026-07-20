import { BrainCircuit } from "lucide-react"

import { siteConfig } from "@/config/site"
import { cn } from "@/lib/utils"

export function BrandMark({
  className,
}: Readonly<{ className?: string }>) {
  return (
    <span
      className={cn(
        "flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-violet-500 text-primary-foreground shadow-lg shadow-primary/20",
        className,
      )}
      aria-hidden="true"
    >
      <BrainCircuit className="size-5" />
    </span>
  )
}

export function BrandWordmark({
  compact = false,
  className,
}: Readonly<{ compact?: boolean; className?: string }>) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <BrandMark />
      <div className="min-w-0">
        <p className="truncate font-heading font-semibold tracking-tight">
          {compact ? siteConfig.shortName : siteConfig.name}
        </p>
        {!compact && (
          <p className="truncate text-xs text-muted-foreground">
            Enterprise knowledge intelligence
          </p>
        )}
      </div>
    </div>
  )
}

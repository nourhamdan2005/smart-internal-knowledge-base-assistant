import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: Readonly<{
  eyebrow?: string
  title: string
  description?: string
  actions?: React.ReactNode
  className?: string
}>) {
  return (
    <header
      className={cn(
        "flex flex-col gap-5 border-b pb-6 sm:flex-row sm:items-end sm:justify-between",
        className,
      )}
    >
      <div className="max-w-3xl">
        {eyebrow && (
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            {eyebrow}
          </p>
        )}
        <h1 className="text-balance font-heading text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-3 text-pretty leading-7 text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  )
}

export function SectionHeader({
  title,
  description,
  icon: Icon,
  action,
  className,
}: Readonly<{
  title: string
  description?: string
  icon?: LucideIcon
  action?: React.ReactNode
  className?: string
}>) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="size-4" aria-hidden="true" />
          </span>
        )}
        <div>
          <h2 className="font-heading text-lg font-semibold tracking-tight">
            {title}
          </h2>
          {description && (
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      </div>
      {action}
    </div>
  )
}

export function MetadataList({
  items,
  className,
}: Readonly<{
  items: ReadonlyArray<{ label: string; value: React.ReactNode }>
  className?: string
}>) {
  return (
    <dl className={cn("divide-y", className)}>
      {items.map(({ label, value }) => (
        <div
          key={label}
          className="grid gap-1 py-3 sm:grid-cols-[10rem_1fr] sm:gap-4"
        >
          <dt className="text-sm font-medium text-muted-foreground">
            {label}
          </dt>
          <dd className="text-sm text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

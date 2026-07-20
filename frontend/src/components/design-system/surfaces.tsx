import type { LucideIcon } from "lucide-react"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export function GradientIcon({
  icon: Icon,
  className,
}: Readonly<{ icon: LucideIcon; className?: string }>) {
  return (
    <span
      className={cn(
        "flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/18 to-violet-500/18 text-primary ring-1 ring-primary/15",
        className,
      )}
    >
      <Icon className="size-5" aria-hidden="true" />
    </span>
  )
}

export function GlassPanel({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "rounded-2xl border bg-card/72 shadow-[0_24px_80px_-42px_oklch(0.42_0.18_275/0.45)] backdrop-blur-xl",
        className,
      )}
      {...props}
    />
  )
}

export function StatCard({
  label,
  value,
  change,
  icon,
  className,
}: Readonly<{
  label: string
  value: React.ReactNode
  change?: React.ReactNode
  icon: LucideIcon
  className?: string
}>) {
  return (
    <Card className={cn("transition-[transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:shadow-lg", className)}>
      <CardHeader className="flex-row items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <GradientIcon icon={icon} className="size-9 rounded-lg [&_svg]:size-4" />
      </CardHeader>
      <CardContent>
        <p className="font-heading text-3xl font-semibold tracking-tight">
          {value}
        </p>
        {change && (
          <div className="mt-2 text-xs text-muted-foreground">{change}</div>
        )}
      </CardContent>
    </Card>
  )
}

export function FeatureCard({
  icon,
  title,
  description,
  footer,
  className,
}: Readonly<{
  icon: LucideIcon
  title: string
  description: string
  footer?: React.ReactNode
  className?: string
}>) {
  return (
    <Card className={cn("h-full transition-[transform,box-shadow] duration-200 hover:-translate-y-1 hover:shadow-xl", className)}>
      <CardHeader>
        <GradientIcon icon={icon} />
        <h3 className="mt-5 font-heading text-base font-semibold">{title}</h3>
        <p className="text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </CardHeader>
      {footer && <CardContent className="mt-auto">{footer}</CardContent>}
    </Card>
  )
}

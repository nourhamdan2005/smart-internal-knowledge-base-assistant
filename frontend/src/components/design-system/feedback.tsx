"use client"

import { useState } from "react"
import {
  AlertTriangle,
  Bot,
  Inbox,
  LoaderCircle,
  RefreshCw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

export function InlineSpinner({
  label = "Loading",
  className,
}: Readonly<{ label?: string; className?: string }>) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LoaderCircle className="size-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </span>
  )
}

type StateProps = {
  title: string
  description: string
  action?: React.ReactNode
  compact?: boolean
}

export function EmptyState({
  title,
  description,
  action,
  compact = false,
}: Readonly<StateProps>) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-2xl border border-dashed bg-muted/20 px-6 text-center", compact ? "py-8" : "py-14")}>
      <span className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <Inbox className="size-5" aria-hidden="true" />
      </span>
      <h3 className="font-heading font-semibold">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function ErrorState({
  title,
  description,
  action,
  compact = false,
}: Readonly<StateProps>) {
  return (
    <div role="alert" className={cn("flex flex-col items-center justify-center rounded-2xl border border-destructive/20 bg-destructive/5 px-6 text-center", compact ? "py-8" : "py-14")}>
      <span className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <AlertTriangle className="size-5" aria-hidden="true" />
      </span>
      <h3 className="font-heading font-semibold">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function LoadingState({
  label = "Loading workspace",
  fullPage = false,
}: Readonly<{ label?: string; fullPage?: boolean }>) {
  return (
    <div
      role="status"
      className={cn(
        "flex flex-col items-center justify-center gap-4",
        fullPage ? "min-h-[60vh]" : "rounded-2xl border py-12",
      )}
    >
      <span className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <LoaderCircle className="size-5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
      </span>
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  )
}

export function ProgressState({
  label,
  value,
  detail,
}: Readonly<{ label: string; value: number; detail?: string }>) {
  return (
    <div className="space-y-3 rounded-xl border bg-card p-4">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="font-medium">{label}</span>
        <span className="tabular-nums text-muted-foreground">{value}%</span>
      </div>
      <Progress value={value} aria-label={`${label}: ${value}%`} />
      {detail && <p className="text-xs text-muted-foreground">{detail}</p>}
    </div>
  )
}

export function AiTypingIndicator() {
  return (
    <div role="status" className="inline-flex items-center gap-3 rounded-2xl border bg-card px-4 py-3 shadow-sm">
      <Bot className="size-4 text-primary" aria-hidden="true" />
      <span className="flex gap-1" aria-hidden="true">
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className="size-1.5 animate-bounce rounded-full bg-primary motion-reduce:animate-none"
            style={{ animationDelay: `${index * 120}ms` }}
          />
        ))}
      </span>
      <span className="sr-only">AI is composing a response</span>
    </div>
  )
}

export function ConfirmActionDialog({
  trigger,
  title,
  description,
  confirmLabel = "Confirm",
  destructive = false,
  onConfirm,
}: Readonly<{
  trigger: React.ReactNode
  title: string
  description: string
  confirmLabel?: string
  destructive?: boolean
  onConfirm?: () => void
}>) {
  const [open, setOpen] = useState(false)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger as React.ReactElement} />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
          <Button
            variant={destructive ? "destructive" : "default"}
            onClick={() => {
              onConfirm?.()
              setOpen(false)
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function RetryButton({
  onClick,
}: Readonly<{ onClick?: () => void }>) {
  return (
    <Button variant="outline" onClick={onClick}>
      <RefreshCw data-icon="inline-start" />
      Try again
    </Button>
  )
}

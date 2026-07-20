"use client"

import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Filter,
  Search,
  X,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

export function SearchField({
  label = "Search",
  className,
  ...props
}: Readonly<
  Omit<React.ComponentProps<typeof InputGroupInput>, "type"> & {
    label?: string
    className?: string
  }
>) {
  return (
    <InputGroup className={cn("w-full sm:max-w-sm", className)}>
      <InputGroupAddon>
        <Search aria-hidden="true" />
      </InputGroupAddon>
      <InputGroupInput type="search" aria-label={label} placeholder={label} {...props} />
    </InputGroup>
  )
}

export function FilterToolbar({
  children,
  label = "Filters",
  className,
}: Readonly<{
  children: React.ReactNode
  label?: string
  className?: string
}>) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn("flex flex-wrap items-center gap-2", className)}
    >
      <Filter className="size-4 text-muted-foreground" aria-hidden="true" />
      {children}
    </div>
  )
}

export function DataViewToolbar({
  search,
  filters,
  actions,
  className,
}: Readonly<{
  search?: React.ReactNode
  filters?: React.ReactNode
  actions?: React.ReactNode
  className?: string
}>) {
  return (
    <div className={cn("grid gap-3 rounded-2xl border bg-card p-3 lg:grid-cols-[minmax(16rem,1fr)_auto_auto] lg:items-center", className)}>
      <div>{search}</div>
      <div className="min-w-0 overflow-x-auto">{filters}</div>
      {actions && <div className="flex flex-wrap justify-start gap-2 lg:justify-end">{actions}</div>}
    </div>
  )
}

export function TableToolbar(props: React.ComponentProps<typeof DataViewToolbar>) {
  return <DataViewToolbar {...props} />
}

export function ResponsiveDataTableContainer({
  children,
  mobileFallback,
  className,
}: Readonly<{
  children: React.ReactNode
  mobileFallback?: React.ReactNode
  className?: string
}>) {
  return (
    <>
      <div className={cn("hidden overflow-hidden rounded-2xl border bg-card md:block", className)}>
        <div className="overflow-x-auto">{children}</div>
      </div>
      {mobileFallback && <div className="grid gap-3 md:hidden">{mobileFallback}</div>}
    </>
  )
}

export function MobileCardFallback({
  title,
  metadata,
  actions,
  children,
}: Readonly<{
  title: string
  metadata?: React.ReactNode
  actions?: React.ReactNode
  children?: React.ReactNode
}>) {
  return (
    <article className="min-w-0 rounded-2xl border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="break-words font-medium">{title}</h3>
          {metadata && <div className="mt-1 text-xs text-muted-foreground">{metadata}</div>}
        </div>
        {actions}
      </div>
      {children && <div className="mt-4">{children}</div>}
    </article>
  )
}

export function SortIndicator({
  direction,
}: Readonly<{ direction?: "ascending" | "descending" }>) {
  const Icon =
    direction === "ascending"
      ? ArrowUp
      : direction === "descending"
        ? ArrowDown
        : ArrowUpDown

  return (
    <Icon
      className="size-3.5 text-muted-foreground"
      aria-label={direction ? `Sorted ${direction}` : "Not sorted"}
    />
  )
}

export function FilterBadge({
  label,
  value,
  onRemove,
}: Readonly<{ label: string; value: string; onRemove?: () => void }>) {
  return (
    <Badge variant="secondary" className="gap-1.5">
      <span className="text-muted-foreground">{label}:</span> {value}
      {onRemove && (
        <button
          type="button"
          className="-mr-1 rounded-full p-0.5 hover:bg-foreground/10 focus-visible:outline-2 focus-visible:outline-ring"
          onClick={onRemove}
          aria-label={`Remove ${label} filter`}
        >
          <X className="size-3" aria-hidden="true" />
        </button>
      )}
    </Badge>
  )
}

export function PaginationControls({
  page,
  pageCount,
  onPrevious,
  onNext,
}: Readonly<{
  page: number
  pageCount: number
  onPrevious?: () => void
  onNext?: () => void
}>) {
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-4">
      <p className="text-sm text-muted-foreground">
        Page <span className="font-medium text-foreground">{page}</span> of {pageCount}
      </p>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="icon-sm"
          onClick={onPrevious}
          disabled={page <= 1}
          aria-label={`Go to page ${Math.max(1, page - 1)}`}
        >
          <ChevronLeft />
        </Button>
        <Button
          variant="outline"
          size="icon-sm"
          onClick={onNext}
          disabled={page >= pageCount}
          aria-label={`Go to page ${page + 1}`}
        >
          <ChevronRight />
        </Button>
      </div>
    </nav>
  )
}

export function DetailsDrawerShell({
  trigger,
  title,
  description,
  children,
  footer,
}: Readonly<{
  trigger: React.ReactElement
  title: string
  description?: string
  children: React.ReactNode
  footer?: React.ReactNode
}>) {
  return (
    <Sheet>
      <SheetTrigger render={trigger} />
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader className="border-b">
          <SheetTitle>{title}</SheetTitle>
          {description && <SheetDescription>{description}</SheetDescription>}
        </SheetHeader>
        <div className="flex-1 overflow-y-auto px-4">{children}</div>
        {footer && <div className="border-t p-4">{footer}</div>}
      </SheetContent>
    </Sheet>
  )
}

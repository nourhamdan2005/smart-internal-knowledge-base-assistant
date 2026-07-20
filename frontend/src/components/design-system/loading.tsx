import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

export function CardSkeleton({ className }: Readonly<{ className?: string }>) {
  return (
    <div className={cn("space-y-5 rounded-2xl border bg-card p-5", className)}>
      <Skeleton className="size-10 rounded-xl" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-2/5" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
    </div>
  )
}

export function PageSkeleton() {
  return (
    <div role="status" aria-label="Loading page" className="mx-auto max-w-7xl space-y-8 px-6 py-10">
      <div className="space-y-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-10 w-full max-w-md" />
        <Skeleton className="h-4 w-full max-w-xl" />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <CardSkeleton key={item} />
        ))}
      </div>
    </div>
  )
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
}: Readonly<{ rows?: number; columns?: number }>) {
  return (
    <div role="status" aria-label="Loading table" className="overflow-hidden rounded-2xl border">
      <div className="grid gap-4 border-b bg-muted/40 p-4" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
        {Array.from({ length: columns }, (_, column) => (
          <Skeleton key={column} className="h-3 w-3/4" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, row) => (
        <div
          key={row}
          className="grid gap-4 border-b p-4 last:border-0"
          style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
        >
          {Array.from({ length: columns }, (_, column) => (
            <Skeleton key={column} className="h-4 w-full" />
          ))}
        </div>
      ))}
    </div>
  )
}

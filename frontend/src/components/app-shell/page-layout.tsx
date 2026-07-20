import { cn } from "@/lib/utils"

export function AppPageContainer({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8", className)}
      {...props}
    />
  )
}

export function AppPageSection({
  className,
  ...props
}: React.ComponentProps<"section">) {
  return (
    <section
      className={cn("rounded-2xl border bg-card p-5 shadow-sm sm:p-6", className)}
      {...props}
    />
  )
}

export function AppContentGrid({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-3", className)}
      {...props}
    />
  )
}

export function AppTwoColumnLayout({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]", className)}
      {...props}
    />
  )
}

"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { ShieldCheck } from "lucide-react"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { BrandWordmark } from "@/components/design-system/brand"
import { LoadingState } from "@/components/design-system/feedback"
import { CheckboxField, PasswordField, SubmitButton, TextField } from "@/components/design-system/forms"
import { ThemeToggle } from "@/components/theme-toggle"
import { APP_ROUTES } from "@/constants"
import type { NormalizedApiError } from "@/lib/api/client"

import { useAuth } from "./auth-provider"

const loginSchema = z.object({
  email: z.email("Enter a valid work email.").max(254),
  password: z.string().min(1, "Enter your password.").max(1024),
  rememberMe: z.boolean(),
})

type LoginValues = z.infer<typeof loginSchema>

export function LoginForm() {
  const { login, status } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const returnTo = searchParams.get("returnTo")
  const destination = returnTo?.startsWith("/") && !returnTo.startsWith("//")
    ? returnTo
    : APP_ROUTES.dashboard
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", rememberMe: true },
  })

  useEffect(() => {
    if (status === "authenticated") router.replace(destination)
  }, [destination, router, status])

  async function onSubmit(values: LoginValues) {
    try {
      await login(values)
      toast.success("Welcome back.")
      router.replace(destination)
    } catch (error) {
      const normalized = error as NormalizedApiError
      const message = normalized.status === 401
        ? "The email or password is incorrect."
        : normalized.status === 503
          ? "Authentication is temporarily unavailable."
          : normalized.isNetworkError
            ? "Cannot reach the authentication service."
            : normalized.message
      form.setError("root", { message })
    }
  }

  if (status === "initializing" || status === "authenticated") {
    return <LoadingState fullPage label="Checking your session" />
  }

  return (
    <main className="grid min-h-svh lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-indigo-700 via-violet-700 to-purple-800 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle_at_20%_20%,white_0_1px,transparent_1.5px)] [background-size:32px_32px]" aria-hidden="true" />
        <div className="relative"><BrandWordmark className="[&_p]:text-white [&_p:last-child]:text-white/70" /></div>
        <div className="relative max-w-xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-white/70">Secure enterprise intelligence</p>
          <p className="mt-5 text-5xl font-semibold tracking-[-0.045em]">Your company knowledge, instantly accessible.</p>
          <p className="mt-6 text-lg leading-8 text-white/75">Grounded answers from approved internal documentation, protected by role-based access and traceable sources.</p>
          <p className="mt-8 flex items-center gap-2 text-sm text-white/80"><ShieldCheck className="size-4" />JWT-secured access with authoritative user validation</p>
        </div>
      </section>
      <section className="relative flex items-center justify-center px-5 py-12 sm:px-8">
        <div className="absolute right-5 top-5"><ThemeToggle /></div>
        <div className="w-full max-w-md">
          <div className="mb-9 lg:hidden"><BrandWordmark /></div>
          <h1 className="font-heading text-3xl font-semibold tracking-tight">Welcome back</h1>
          <p className="mt-2 text-sm text-muted-foreground">Sign in with your CGC Knowledge AI account.</p>
          <form className="mt-8 space-y-5" onSubmit={form.handleSubmit(onSubmit)}>
            <TextField label="Work email" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register("email")} />
            <PasswordField label="Password" autoComplete="current-password" error={form.formState.errors.password?.message} {...form.register("password")} />
            <div className="flex items-center justify-between gap-4">
              <Controller
                control={form.control}
                name="rememberMe"
                render={({ field }) => (
                  <CheckboxField
                    label="Remember me"
                    checked={field.value}
                    onCheckedChange={(checked) => field.onChange(checked === true)}
                  />
                )}
              />
            </div>
            {form.formState.errors.root?.message && <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{form.formState.errors.root.message}</p>}
            <SubmitButton className="w-full" size="lg" loading={form.formState.isSubmitting} loadingLabel="Signing in">Sign in</SubmitButton>
          </form>
        </div>
      </section>
    </main>
  )
}

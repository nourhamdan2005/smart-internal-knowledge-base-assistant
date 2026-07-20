"use client"

import { useId, useState } from "react"
import { Eye, EyeOff } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  InputGroup,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

import { InlineSpinner } from "./feedback"

type FieldFrameProps = {
  label: string
  htmlFor: string
  description?: string
  error?: string
  required?: boolean
  children: React.ReactNode
  className?: string
}

export function RequiredIndicator() {
  return (
    <span className="text-destructive" aria-hidden="true">
      *
    </span>
  )
}

export function FieldFrame({
  label,
  htmlFor,
  description,
  error,
  required,
  children,
  className,
}: Readonly<FieldFrameProps>) {
  const descriptionId = description ? `${htmlFor}-description` : undefined
  const errorId = error ? `${htmlFor}-error` : undefined

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={htmlFor}>
        {label} {required && <RequiredIndicator />}
      </Label>
      {children}
      {description && (
        <p id={descriptionId} className="text-xs leading-5 text-muted-foreground">
          {description}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-xs font-medium text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}

type TextFieldProps = Omit<React.ComponentProps<typeof Input>, "id"> & {
  id?: string
  label: string
  description?: string
  error?: string
}

export function TextField({
  id,
  label,
  description,
  error,
  required,
  className,
  ...props
}: Readonly<TextFieldProps>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId

  return (
    <FieldFrame
      label={label}
      htmlFor={fieldId}
      description={description}
      error={error}
      required={required}
    >
      <Input
        id={fieldId}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={
          error
            ? `${fieldId}-error`
            : description
              ? `${fieldId}-description`
              : undefined
        }
        className={className}
        {...props}
      />
    </FieldFrame>
  )
}

export function PasswordField({
  id,
  label,
  description,
  error,
  required,
  ...props
}: Readonly<Omit<TextFieldProps, "type">>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId
  const [visible, setVisible] = useState(false)

  return (
    <FieldFrame
      label={label}
      htmlFor={fieldId}
      description={description}
      error={error}
      required={required}
    >
      <InputGroup>
        <InputGroupInput
          id={fieldId}
          type={visible ? "text" : "password"}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error
              ? `${fieldId}-error`
              : description
                ? `${fieldId}-description`
                : undefined
          }
          {...props}
        />
        <InputGroupButton
          size="icon-xs"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
        >
          {visible ? <EyeOff /> : <Eye />}
        </InputGroupButton>
      </InputGroup>
    </FieldFrame>
  )
}

type TextareaFieldProps = Omit<React.ComponentProps<typeof Textarea>, "id"> & {
  id?: string
  label: string
  description?: string
  error?: string
}

export function TextareaField({
  id,
  label,
  description,
  error,
  required,
  ...props
}: Readonly<TextareaFieldProps>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId

  return (
    <FieldFrame
      label={label}
      htmlFor={fieldId}
      description={description}
      error={error}
      required={required}
    >
      <Textarea
        id={fieldId}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        {...props}
      />
    </FieldFrame>
  )
}

type SelectOption = { label: string; value: string }

export function SelectField({
  id,
  label,
  options,
  placeholder = "Select an option",
  description,
  error,
  required,
  value,
  defaultValue,
  onValueChange,
  disabled,
}: Readonly<{
  id?: string
  label: string
  options: SelectOption[]
  placeholder?: string
  description?: string
  error?: string
  required?: boolean
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
}>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId

  return (
    <FieldFrame
      label={label}
      htmlFor={fieldId}
      description={description}
      error={error}
      required={required}
    >
      <Select
        value={value}
        defaultValue={defaultValue}
        onValueChange={(nextValue) => onValueChange?.(nextValue ?? "")}
        disabled={disabled}
        required={required}
      >
        <SelectTrigger
          id={fieldId}
          className="w-full"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${fieldId}-error` : undefined}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FieldFrame>
  )
}

export function CheckboxField({
  id,
  label,
  description,
  ...props
}: Readonly<
  React.ComponentProps<typeof Checkbox> & {
    label: string
    description?: string
  }
>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId

  return (
    <div className="flex items-start gap-3">
      <Checkbox id={fieldId} className="mt-0.5" {...props} />
      <div className="grid gap-1">
        <Label htmlFor={fieldId}>{label}</Label>
        {description && (
          <p className="text-xs leading-5 text-muted-foreground">{description}</p>
        )}
      </div>
    </div>
  )
}

export function SwitchField({
  id,
  label,
  description,
  ...props
}: Readonly<
  React.ComponentProps<typeof Switch> & {
    label: string
    description?: string
  }
>) {
  const generatedId = useId()
  const fieldId = id ?? generatedId

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border p-4">
      <div className="grid gap-1">
        <Label htmlFor={fieldId}>{label}</Label>
        {description && (
          <p className="text-xs leading-5 text-muted-foreground">{description}</p>
        )}
      </div>
      <Switch id={fieldId} {...props} />
    </div>
  )
}

export function FormSection({
  title,
  description,
  children,
  className,
}: Readonly<{
  title: string
  description?: string
  children: React.ReactNode
  className?: string
}>) {
  return (
    <fieldset className={cn("grid gap-5 rounded-2xl border bg-card p-5", className)}>
      <legend className="sr-only">{title}</legend>
      <div>
        <h3 className="font-heading font-semibold">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </fieldset>
  )
}

export function SubmitButton({
  loading,
  loadingLabel = "Saving",
  children,
  disabled,
  ...props
}: Readonly<
  React.ComponentProps<typeof Button> & {
    loading?: boolean
    loadingLabel?: string
  }
>) {
  return (
    <Button type="submit" disabled={disabled || loading} {...props}>
      {loading && <InlineSpinner label={loadingLabel} />}
      {loading ? loadingLabel : children}
    </Button>
  )
}

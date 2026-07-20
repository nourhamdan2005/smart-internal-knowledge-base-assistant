"use client"

import { useMemo, useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm, useWatch } from "react-hook-form"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, UserMinus } from "lucide-react"
import { toast } from "sonner"
import { z } from "zod"

import { AppPageContainer, UserIdentity } from "@/components/app-shell"
import { DataViewToolbar, MobileCardFallback, ResponsiveDataTableContainer, SearchField } from "@/components/design-system/data-view"
import { ConfirmActionDialog, EmptyState, ErrorState } from "@/components/design-system/feedback"
import { PasswordField, SelectField, SubmitButton, SwitchField, TextField } from "@/components/design-system/forms"
import { MetadataList, PageHeader } from "@/components/design-system/layout"
import { TableSkeleton } from "@/components/design-system/loading"
import { RoleBadge, StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { USER_ROLES, type UserRole } from "@/constants"
import { useAuth, type AuthenticatedUser } from "@/features/auth"
import { dashboardKeys } from "@/features/dashboard/api"
import type { NormalizedApiError } from "@/lib/api/client"

import { createManagedUser, deactivateManagedUser, listManagedUsers, updateManagedUser, userKeys } from "./api"
import type { ManagedUser } from "./types"

const createSchema = z.object({
  full_name: z.string().min(1).max(150),
  email: z.email().max(254),
  password: z.string().min(8).max(1024),
  role: z.enum(["admin", "editor", "employee"]),
})
type CreateValues = z.infer<typeof createSchema>

function date(value: string | null) {
  return value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Never"
}

function asIdentity(user: ManagedUser): AuthenticatedUser {
  return { id: user.id, email: user.email, fullName: user.full_name, role: user.role, isActive: user.is_active, createdAt: user.created_at, updatedAt: user.updated_at, lastLoginAt: user.last_login_at }
}

export function UsersView() {
  const queryClient = useQueryClient()
  const auth = useAuth()
  const [search, setSearch] = useState("")
  const [role, setRole] = useState("all")
  const [status, setStatus] = useState("all")
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<ManagedUser | null>(null)
  const [editing, setEditing] = useState<ManagedUser | null>(null)
  const [editRole, setEditRole] = useState<UserRole>("employee")
  const [editActive, setEditActive] = useState(true)
  const form = useForm<CreateValues>({ resolver: zodResolver(createSchema), defaultValues: { full_name: "", email: "", password: "", role: "employee" } })
  const createRole = useWatch({ control: form.control, name: "role" })
  const users = useQuery({ queryKey: userKeys.list(), queryFn: ({ signal }) => listManagedUsers(signal), staleTime: 30_000 })
  const invalidate = async () => Promise.all([queryClient.invalidateQueries({ queryKey: userKeys.all }), queryClient.invalidateQueries({ queryKey: dashboardKeys.users() })])
  const createMutation = useMutation<ManagedUser, NormalizedApiError, CreateValues>({
    mutationFn: createManagedUser,
    onSuccess: async () => { toast.success("User created."); setCreating(false); form.reset(); await invalidate() },
    onError: (error) => form.setError("root", { message: error.status === 409 ? "A user with this email already exists." : error.message }),
  })
  const updateMutation = useMutation<ManagedUser, NormalizedApiError, { id: string; full_name: string; email: string; role: UserRole; is_active: boolean }>({
    mutationFn: ({ id, ...input }) => updateManagedUser(id, input),
    onSuccess: async (updated) => {
      toast.success("User updated."); setEditing(null); setSelected(updated)
      await invalidate()
      if (updated.id === auth.user?.id) await auth.refreshCurrentUser()
    },
    onError: (error) => toast.error(error.status === 409 ? error.message : "The user could not be updated."),
  })
  const deactivateMutation = useMutation<void, NormalizedApiError, string>({
    mutationFn: deactivateManagedUser,
    onSuccess: async () => { toast.success("User deactivated."); setSelected(null); await invalidate() },
    onError: (error) => toast.error(error.status === 409 ? error.message : "The user could not be deactivated."),
  })
  const filtered = useMemo(() => (users.data ?? []).filter((user) => {
    const matchesSearch = `${user.full_name} ${user.email}`.toLowerCase().includes(search.toLowerCase())
    return matchesSearch && (role === "all" || user.role === role) && (status === "all" || user.is_active === (status === "active"))
  }), [role, search, status, users.data])

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader eyebrow="Administration" title="User Management" description="Manage the first 100 accounts returned by the administration API." actions={<Button onClick={() => setCreating(true)}><Plus />Create user</Button>} />
      <DataViewToolbar search={<SearchField label="Search current users" value={search} onChange={(event) => setSearch(event.target.value)} />} filters={<div className="flex gap-2"><Select value={role} onValueChange={(value) => setRole(value ?? "all")}><SelectTrigger className="w-36" aria-label="Filter by role"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All roles</SelectItem><SelectItem value="admin">Admin</SelectItem><SelectItem value="editor">Editor</SelectItem><SelectItem value="employee">Employee</SelectItem></SelectContent></Select><Select value={status} onValueChange={(value) => setStatus(value ?? "all")}><SelectTrigger className="w-36" aria-label="Filter by status"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All statuses</SelectItem><SelectItem value="active">Active</SelectItem><SelectItem value="inactive">Inactive</SelectItem></SelectContent></Select></div>} />
      <p className="text-sm text-muted-foreground">{filtered.length} matching {filtered.length === 1 ? "user" : "users"}</p>
      {users.isLoading ? <TableSkeleton /> : users.isError ? <ErrorState title="Users could not be loaded" description="Retry the current administration request." action={<Button onClick={() => void users.refetch()}>Retry</Button>} /> : filtered.length === 0 ? <EmptyState title="No matching users" description="Adjust the current search or filters." /> : <ResponsiveDataTableContainer mobileFallback={filtered.map((user) => <MobileCardFallback key={user.id} title={user.full_name} metadata={user.email} actions={<Button size="sm" variant="outline" onClick={() => setSelected(user)}>Details</Button>}><div className="flex gap-2"><RoleBadge role={user.role} /><StatusBadge tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Inactive"}</StatusBadge></div></MobileCardFallback>)}><Table><TableHeader><TableRow><TableHead>User</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead>Last login</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader><TableBody>{filtered.map((user) => <TableRow key={user.id}><TableCell><p className="font-medium">{user.full_name}</p><p className="text-xs text-muted-foreground">{user.email}</p></TableCell><TableCell><RoleBadge role={user.role} /></TableCell><TableCell><StatusBadge tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Inactive"}</StatusBadge></TableCell><TableCell>{date(user.last_login_at)}</TableCell><TableCell className="text-right"><Button size="sm" variant="outline" onClick={() => setSelected(user)}>Details</Button></TableCell></TableRow>)}</TableBody></Table></ResponsiveDataTableContainer>}

      <Dialog open={creating} onOpenChange={setCreating}><DialogContent><DialogHeader><DialogTitle>Create user</DialogTitle><DialogDescription>Create an active account with a supported role.</DialogDescription></DialogHeader><form className="space-y-4" onSubmit={form.handleSubmit((values) => createMutation.mutate(values))}><TextField label="Full name" error={form.formState.errors.full_name?.message} {...form.register("full_name")} /><TextField label="Email" type="email" error={form.formState.errors.email?.message} {...form.register("email")} /><PasswordField label="Temporary password" error={form.formState.errors.password?.message} {...form.register("password")} /><SelectField label="Role" value={createRole} onValueChange={(value) => form.setValue("role", value as UserRole, { shouldValidate: true })} options={[{ label: "Employee", value: "employee" },{ label: "Editor", value: "editor" },{ label: "Admin", value: "admin" }]} />{form.formState.errors.root?.message && <p role="alert" className="text-sm text-destructive">{form.formState.errors.root.message}</p>}<SubmitButton loading={createMutation.isPending}>Create user</SubmitButton></form></DialogContent></Dialog>

      <Sheet open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}><SheetContent className="w-full sm:max-w-md"><SheetHeader className="border-b"><SheetTitle>User details</SheetTitle></SheetHeader>{selected && <div className="space-y-6 px-4"><UserIdentity user={asIdentity(selected)} showRole /><MetadataList items={[{ label: "Status", value: selected.is_active ? "Active" : "Inactive" },{ label: "Created", value: date(selected.created_at) },{ label: "Updated", value: date(selected.updated_at) },{ label: "Last login", value: date(selected.last_login_at) },{ label: "User ID", value: <span className="break-all">{selected.id}</span> }]} /><div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => { setEditing(selected); setEditRole(selected.role); setEditActive(selected.is_active) }}><Pencil />Edit</Button>{selected.is_active && <ConfirmActionDialog trigger={<Button variant="destructive"><UserMinus />Deactivate</Button>} title={`Deactivate ${selected.full_name}?`} description="This endpoint deactivates the account; it does not permanently erase the user record." destructive confirmLabel="Deactivate user" onConfirm={() => deactivateMutation.mutate(selected.id)} />}</div></div>}</SheetContent></Sheet>

      <Dialog open={editing !== null} onOpenChange={(open) => !open && setEditing(null)}><DialogContent><DialogHeader><DialogTitle>Edit user</DialogTitle><DialogDescription>Update supported identity, role, and active-state fields.</DialogDescription></DialogHeader>{editing && <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); updateMutation.mutate({ id: editing.id, full_name: String(data.get("full_name")), email: String(data.get("email")), role: editRole, is_active: editActive }) }}><TextField label="Full name" name="full_name" defaultValue={editing.full_name} required maxLength={150} /><TextField label="Email" name="email" type="email" defaultValue={editing.email} required /><SelectField label="Role" value={editRole} onValueChange={(value) => setEditRole(value as UserRole)} options={[{ label: "Employee", value: USER_ROLES.employee },{ label: "Editor", value: USER_ROLES.editor },{ label: "Admin", value: USER_ROLES.admin }]} /><SwitchField label="Active account" description="Deactivating an account immediately blocks future authenticated access." checked={editActive} onCheckedChange={setEditActive} /><SubmitButton loading={updateMutation.isPending}>Save user</SubmitButton></form>}</DialogContent></Dialog>
    </AppPageContainer>
  )
}

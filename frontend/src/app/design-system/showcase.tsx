"use client"

import { Activity, BookOpen, Database, FileText, Plus, ShieldCheck, Sparkles, Users } from "lucide-react"

import { BrandWordmark } from "@/components/design-system/brand"
import {
  DataViewToolbar,
  DetailsDrawerShell,
  FilterBadge,
  FilterToolbar,
  MobileCardFallback,
  PaginationControls,
  ResponsiveDataTableContainer,
  SearchField,
  SortIndicator,
} from "@/components/design-system/data-view"
import {
  AiTypingIndicator,
  ConfirmActionDialog,
  EmptyState,
  ErrorState,
  InlineSpinner,
  LoadingState,
  ProgressState,
  RetryButton,
} from "@/components/design-system/feedback"
import {
  CheckboxField,
  FormSection,
  PasswordField,
  SelectField,
  SubmitButton,
  SwitchField,
  TextareaField,
  TextField,
} from "@/components/design-system/forms"
import { MetadataList, PageHeader, SectionHeader } from "@/components/design-system/layout"
import { CardSkeleton, TableSkeleton } from "@/components/design-system/loading"
import { PageEntrance, StaggeredItem, StaggeredList } from "@/components/design-system/motion"
import { FeatureCard, GlassPanel, StatCard } from "@/components/design-system/surfaces"
import { HealthIndicator, RoleBadge, StatusBadge } from "@/components/design-system/status"
import { ThemeToggle } from "@/components/theme-toggle"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const documents = [
  { title: "Remote Work Policy", category: "HR", owner: "People Operations", status: "Indexed" },
  { title: "Security Runbook", category: "IT", owner: "Infrastructure", status: "Processing" },
  { title: "Brand Guidelines", category: "Marketing", owner: "Brand Team", status: "Indexed" },
]

export function DesignSystemShowcase() {
  return (
    <PageEntrance className="min-h-svh bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/88 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 lg:px-8">
          <BrandWordmark />
          <div className="flex items-center gap-3">
            <Badge variant="outline">Internal preview</Badge>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-16 px-5 py-10 lg:px-8 lg:py-14">
        <PageHeader
          eyebrow="Phase 10.2"
          title="CGC Knowledge AI design system"
          description="A responsive, accessible component foundation for focused enterprise knowledge work. This internal route is intentionally excluded from product navigation."
          actions={
            <>
              <Button variant="outline">Secondary action</Button>
              <Button><Plus data-icon="inline-start" />Primary action</Button>
            </>
          }
        />

        <section className="space-y-6">
          <SectionHeader title="Typography and actions" description="Offline-safe type, restrained hierarchy, and consistent interaction states." icon={Sparkles} />
          <GlassPanel className="grid gap-8 p-6 md:grid-cols-2">
            <div className="space-y-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Enterprise intelligence</p>
              <h2 className="text-balance font-heading text-4xl font-semibold tracking-[-0.04em]">Knowledge that moves at the speed of work.</h2>
              <p className="max-w-xl leading-7 text-muted-foreground">Clear typography keeps dense operational information readable without feeling clinical or generic.</p>
            </div>
            <div className="flex flex-wrap content-start gap-2">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
              <Button disabled>Disabled</Button>
            </div>
          </GlassPanel>
        </section>

        <section className="space-y-6">
          <SectionHeader title="Cards and surfaces" description="Composable content surfaces for metrics and feature summaries." icon={Activity} />
          <StaggeredList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StaggeredItem><StatCard label="Indexed documents" value="1,284" change="+8.2% this month" icon={FileText} /></StaggeredItem>
            <StaggeredItem><StatCard label="Knowledge queries" value="8,492" change="94% grounded answers" icon={BookOpen} /></StaggeredItem>
            <StaggeredItem><StatCard label="Active users" value="327" change="Across 14 departments" icon={Users} /></StaggeredItem>
          </StaggeredList>
          <div className="grid gap-4 md:grid-cols-3">
            <FeatureCard icon={Database} title="Grounded retrieval" description="Pairs semantic discovery with keyword precision and traceable sources." />
            <FeatureCard icon={ShieldCheck} title="Role-aware access" description="Thin presentation wrappers stay independent from authorization and API data." />
            <FeatureCard icon={Sparkles} title="Private intelligence" description="A calm visual language supports AI workflows without decorative excess." />
          </div>
        </section>

        <section className="space-y-6">
          <SectionHeader title="Status and feedback" description="Semantic states remain understandable without relying on color alone." icon={Activity} />
          <Card>
            <CardHeader>
              <CardTitle>Badges and health</CardTitle>
              <CardDescription>Reusable labels for roles, workflows, and service state.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3">
              <RoleBadge role="admin" /><RoleBadge role="editor" /><RoleBadge role="employee" />
              <StatusBadge tone="success">Indexed</StatusBadge>
              <StatusBadge tone="warning">Processing</StatusBadge>
              <StatusBadge tone="danger">Failed</StatusBadge>
              <HealthIndicator status="healthy" label="API operational" />
              <HealthIndicator status="degraded" label="Vector index delayed" />
            </CardContent>
          </Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <EmptyState title="No matching documents" description="Adjust the current filters or broaden the search phrase." action={<Button variant="outline">Clear filters</Button>} />
            <ErrorState title="Knowledge service unavailable" description="The request could not be completed. Existing content remains safe." action={<RetryButton />} />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <ProgressState label="Indexing handbook.pdf" value={68} detail="Extracting and embedding page 24 of 36." />
            <div className="flex items-center justify-center rounded-2xl border bg-card p-6"><AiTypingIndicator /></div>
            <LoadingState label="Refreshing sources" />
          </div>
        </section>

        <section className="space-y-6">
          <SectionHeader title="Form system" description="Controlled or uncontrolled inputs compose cleanly with React Hook Form and Zod error output." icon={FileText} />
          <form className="grid gap-5 lg:grid-cols-2" onSubmit={(event) => event.preventDefault()}>
            <FormSection title="Document metadata" description="Labels, help text, required indicators, and validation are consistently associated.">
              <TextField label="Document title" placeholder="Employee handbook" required />
              <SelectField
                label="Category"
                placeholder="Choose a category"
                options={[
                  { label: "Human resources", value: "hr" },
                  { label: "Information technology", value: "it" },
                  { label: "Operations", value: "operations" },
                ]}
              />
              <TextareaField label="Description" placeholder="Summarize this knowledge source." rows={4} />
              <CheckboxField label="Notify editors" description="Send an update when indexing completes." defaultChecked />
            </FormSection>
            <FormSection title="Account pattern" description="Password visibility and loading states include accessible labels.">
              <TextField label="Work email" type="email" defaultValue="editor@cgc.example" />
              <PasswordField label="Password" defaultValue="knowledge-ai" />
              <TextField label="Validation example" defaultValue="Invalid value" error="Use a recognized department code." />
              <SwitchField label="Semantic retrieval" description="Include vector similarity in search ranking." defaultChecked />
              <div className="flex flex-wrap gap-2">
                <SubmitButton>Save changes</SubmitButton>
                <SubmitButton loading loadingLabel="Saving" />
              </div>
            </FormSection>
          </form>
        </section>

        <section className="space-y-6">
          <SectionHeader title="Data-view patterns" description="Toolbars and content adapt from a full table to compact mobile cards." icon={Database} />
          <DataViewToolbar
            search={<SearchField label="Search documents" />}
            filters={<FilterToolbar><FilterBadge label="Category" value="HR" /><FilterBadge label="Status" value="Indexed" /></FilterToolbar>}
            actions={<Button><Plus data-icon="inline-start" />Add document</Button>}
          />
          <ResponsiveDataTableContainer
            mobileFallback={documents.map((document) => (
              <MobileCardFallback key={document.title} title={document.title} metadata={`${document.category} · ${document.owner}`}>
                <StatusBadge tone={document.status === "Indexed" ? "success" : "warning"}>{document.status}</StatusBadge>
              </MobileCardFallback>
            ))}
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><span className="inline-flex items-center gap-1.5">Document <SortIndicator direction="ascending" /></span></TableHead>
                  <TableHead>Category</TableHead><TableHead>Owner</TableHead><TableHead>Status</TableHead>
                  <TableHead className="text-right">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((document) => (
                  <TableRow key={document.title}>
                    <TableCell className="font-medium">{document.title}</TableCell>
                    <TableCell>{document.category}</TableCell>
                    <TableCell>{document.owner}</TableCell>
                    <TableCell><StatusBadge tone={document.status === "Indexed" ? "success" : "warning"}>{document.status}</StatusBadge></TableCell>
                    <TableCell className="text-right">
                      <DetailsDrawerShell
                        trigger={<Button variant="ghost" size="sm">View</Button>}
                        title={document.title}
                        description="Reusable drawer shell for contextual details."
                      >
                        <MetadataList items={[
                          { label: "Category", value: document.category },
                          { label: "Owner", value: document.owner },
                          { label: "Status", value: document.status },
                        ]} />
                      </DetailsDrawerShell>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ResponsiveDataTableContainer>
          <PaginationControls page={1} pageCount={8} />
        </section>

        <section className="space-y-6">
          <SectionHeader title="Loading patterns" description="Skeleton geometry mirrors the surfaces users are waiting for." icon={Sparkles} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
          <TableSkeleton rows={3} />
          <div className="flex flex-wrap items-center gap-4">
            <Button disabled><InlineSpinner />Working</Button>
            <ConfirmActionDialog
              trigger={<Button variant="destructive">Confirm dialog</Button>}
              title="Remove this source?"
              description="This pattern requires a clear consequence and explicit confirmation."
              confirmLabel="Remove source"
              destructive
            />
          </div>
        </section>
      </main>
    </PageEntrance>
  )
}

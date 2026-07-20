"use client"

import { Laptop, Moon, RotateCcw, Settings2, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { toast } from "sonner"

import { AppPageContainer } from "@/components/app-shell"
import { ConfirmActionDialog } from "@/components/design-system/feedback"
import { SelectField, SwitchField } from "@/components/design-system/forms"
import { PageHeader, SectionHeader } from "@/components/design-system/layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { usePreferences } from "@/features/preferences"

const themeOptions = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Laptop },
] as const

export function SettingsView() {
  const { theme, setTheme } = useTheme()
  const { preferences, updatePreference, resetPreferences, hydrated } =
    usePreferences()

  return (
    <AppPageContainer className="space-y-6">
      <PageHeader
        eyebrow="Preferences"
        title="Settings"
        description="Personal display and workflow preferences stored locally in this browser."
        actions={
          <ConfirmActionDialog
            trigger={<Button className="min-h-11" variant="outline"><RotateCcw />Reset preferences</Button>}
            title="Reset application preferences?"
            description="This restores display and workflow defaults. Authentication and chat history are preserved."
            confirmLabel="Reset preferences"
            onConfirm={() => {
              resetPreferences()
              setTheme("system")
              toast.success("Preferences reset.")
            }}
          />
        }
      />
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><SectionHeader title="Appearance" description="Theme selection is shared with the header menu." icon={Sun} /></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {themeOptions.map(({ value, label, icon: Icon }) => (
              <Button
                key={value}
                type="button"
                variant={(theme ?? "system") === value ? "secondary" : "outline"}
                className="h-auto min-h-20 flex-col gap-2"
                aria-pressed={(theme ?? "system") === value}
                onClick={() => setTheme(value)}
              >
                <Icon />{label}
              </Button>
            ))}
            <p className="text-xs leading-5 text-muted-foreground sm:col-span-3">
              System follows your operating system or browser color preference.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><SectionHeader title="Accessibility and motion" description="System mode always honors prefers-reduced-motion." icon={Settings2} /></CardHeader>
          <CardContent>
            <SelectField
              label="Motion preference"
              value={preferences.motion}
              disabled={!hydrated}
              onValueChange={(value) => updatePreference("motion", value as typeof preferences.motion)}
              options={[
                { value: "system", label: "Respect system preference" },
                { value: "reduced", label: "Force reduced motion" },
                { value: "standard", label: "Standard motion" },
              ]}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><SectionHeader title="Workspace defaults" description="Defaults used when opening data-heavy features." icon={Settings2} /></CardHeader>
          <CardContent className="space-y-4">
            <SwitchField label="Expanded sidebar by default" checked={preferences.sidebarExpanded} disabled={!hydrated} onCheckedChange={(value) => updatePreference("sidebarExpanded", value)} />
            <SelectField label="Document default view" value={preferences.documentView} disabled={!hydrated} onValueChange={(value) => updatePreference("documentView", value as typeof preferences.documentView)} options={[{ value: "table", label: "Table" }, { value: "grid", label: "Grid" }]} />
            <SelectField label="Default page size" value={String(preferences.pageSize)} disabled={!hydrated} onValueChange={(value) => updatePreference("pageSize", Number(value) as typeof preferences.pageSize)} options={[10, 20, 50].map((value) => ({ value: String(value), label: `${value} items` }))} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><SectionHeader title="Chat presentation" description="Controls local conversation presentation only." icon={Settings2} /></CardHeader>
          <CardContent className="space-y-4">
            <SelectField label="Message density" value={preferences.chatDensity} disabled={!hydrated} onValueChange={(value) => updatePreference("chatDensity", value as typeof preferences.chatDensity)} options={[{ value: "comfortable", label: "Comfortable" }, { value: "compact", label: "Compact" }]} />
            <SwitchField label="Open source details by default" description="Applies when a cited source is selected." checked={preferences.chatSourcesOpen} disabled={!hydrated} onCheckedChange={(value) => updatePreference("chatSourcesOpen", value)} />
          </CardContent>
        </Card>
      </div>
      <p className="text-xs text-muted-foreground">
        Preferences are versioned and stored only in this browser. The backend currently has no preference synchronization endpoint.
      </p>
    </AppPageContainer>
  )
}

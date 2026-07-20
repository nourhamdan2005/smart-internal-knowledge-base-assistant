"use client"

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { Bot, Copy, Menu, MessageSquarePlus, Pencil, Pin, RefreshCw, Search, Send, Square, ThumbsDown, ThumbsUp, Trash2 } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { toast } from "sonner"

import { AiTypingIndicator, ConfirmActionDialog } from "@/components/design-system/feedback"
import { StatusBadge } from "@/components/design-system/status"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Textarea } from "@/components/ui/textarea"
import { useAuth } from "@/features/auth"
import { usePreferences } from "@/features/preferences"
import { cn } from "@/lib/utils"

import { fullResponseTransport, streamResponse } from "./api"
import { chatHistoryStorage, groupConversations } from "./storage"
import type { ChatMessage, Conversation, SourceCitation } from "./types"

const categories = ["HR", "IT", "Engineering", "API Docs", "Deployment", "Security", "Testing", "Onboarding", "Project Management"]
const suggestions = [
  "What is our remote-work policy?",
  "How should I report a security incident?",
  "Summarize the employee onboarding procedure.",
  "What are the password and MFA requirements?",
]

function id() {
  return crypto.randomUUID()
}

function titleFromPrompt(prompt: string) {
  return prompt.trim().replace(/\s+/g, " ").slice(0, 58)
}

function inlineMarkdown(text: string): ReactNode[] {
  const pattern = /(`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)]+\))/g
  return text.split(pattern).filter(Boolean).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-muted px-1 py-0.5 text-xs">{part.slice(1, -1)}</code>
    }
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/)
    if (link) {
      return <a key={index} href={link[2]} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-4">{link[1]}</a>
    }
    return part
  })
}

function SafeAnswer({ content }: Readonly<{ content: string }>) {
  return (
    <div className="space-y-3 text-sm leading-7">
      {content.split(/\n{2,}/).map((block, index) => {
        const lines = block.split("\n")
        const heading = block.match(/^(#{1,3})\s+(.+)$/)
        if (heading) {
          const level = heading[1].length
          const className = level === 1 ? "text-lg font-semibold" : level === 2 ? "text-base font-semibold" : "font-semibold"
          return <p key={index} role="heading" aria-level={level} className={className}>{inlineMarkdown(heading[2])}</p>
        }
        if (lines.every((line) => line.includes("|")) && lines.length >= 2) {
          const rows = lines.filter((line) => !/^\s*\|?[\s:-]+\|/.test(line)).map((line) => line.replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim()))
          const [headers, ...body] = rows
          return <div key={index} className="overflow-x-auto" tabIndex={0} aria-label="Scrollable answer table"><table className="w-full border-collapse text-left text-xs"><caption className="sr-only">Table included in the AI answer</caption><thead><tr>{headers.map((header, headerIndex) => <th scope="col" key={`${header}-${headerIndex}`} className="border p-2">{inlineMarkdown(header)}</th>)}</tr></thead><tbody>{body.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex} className="border p-2">{inlineMarkdown(cell)}</td>)}</tr>)}</tbody></table></div>
        }
        if (lines.every((line) => line.trim().startsWith("- "))) {
          return <ul key={index} className="list-disc space-y-1 pl-5">{lines.map((line, lineIndex) => <li key={`${line}-${lineIndex}`}>{inlineMarkdown(line.trim().slice(2))}</li>)}</ul>
        }
        if (block.startsWith("```") && block.endsWith("```")) {
          return <pre key={index} tabIndex={0} aria-label="Scrollable code block" className="overflow-x-auto rounded-lg bg-muted p-3 text-xs"><code>{block.replace(/^```[^\n]*\n?/, "").replace(/```$/, "")}</code></pre>
        }
        if (lines.every((line) => line.trim().startsWith(">"))) {
          return <blockquote key={index} className="border-l-2 border-primary pl-4 text-muted-foreground">{inlineMarkdown(lines.map((line) => line.replace(/^\s*>\s?/, "")).join("\n"))}</blockquote>
        }
        return <p key={index} className="whitespace-pre-wrap">{inlineMarkdown(block)}</p>
      })}
    </div>
  )
}

export function ChatView() {
  const { user } = useAuth()
  const { preferences } = usePreferences()
  const searchParams = useSearchParams()
  const initialPrompt = searchParams.get("prompt") ?? ""
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [prompt, setPrompt] = useState(initialPrompt)
  const [category, setCategory] = useState<string>("all")
  const [search, setSearch] = useState("")
  const [historyOpen, setHistoryOpen] = useState(false)
  const [selectedSource, setSelectedSource] = useState<{
    source: SourceCitation
    citation: number
  } | null>(null)
  const hydratedUser = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const composerRef = useRef<HTMLTextAreaElement | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [streamStage, setStreamStage] = useState("Searching company knowledge…")
  const active = conversations.find((conversation) => conversation.id === activeId) ?? null

  useEffect(() => {
    if (!user || hydratedUser.current === user.id) return
    const frame = requestAnimationFrame(() => {
      setConversations(chatHistoryStorage.load(user.id))
      hydratedUser.current = user.id
    })
    return () => cancelAnimationFrame(frame)
  }, [user])

  useEffect(() => {
    if (!user || hydratedUser.current !== user.id) return
    const timer = window.setTimeout(
      () => chatHistoryStorage.save(user.id, conversations),
      250,
    )
    return () => window.clearTimeout(timer)
  }, [conversations, user])

  useEffect(() => () => abortRef.current?.abort(), [])

  const userId = user?.id ?? ""

  function updateConversation(conversationId: string, updater: (conversation: Conversation) => Conversation) {
    setConversations((current) => current.map((conversation) => conversation.id === conversationId ? updater(conversation) : conversation))
  }

  function renameConversation(conversation: Conversation) {
    const nextTitle = window.prompt("Rename conversation", conversation.title)?.trim()
    if (nextTitle) {
      updateConversation(conversation.id, (item) => ({
        ...item,
        title: nextTitle.slice(0, 80),
        updatedAt: new Date().toISOString(),
      }))
    }
  }

  async function send(question = prompt) {
    const clean = question.trim()
    if (!clean || isGenerating) return
    setIsGenerating(true)
    setStreamStage("Searching company knowledge…")
    setPrompt("")
    const now = new Date().toISOString()
    const conversationId = active?.id ?? id()
    const userMessage: ChatMessage = { id: id(), role: "user", content: clean, createdAt: now, status: "complete" }
    const assistantId = id()
    const pending: ChatMessage = { id: assistantId, role: "assistant", content: "", createdAt: now, status: "pending" }
    const selectedCategory = category === "all" ? null : category
    if (!active) {
      setConversations((current) => [{ id: conversationId, userId, title: titleFromPrompt(clean), createdAt: now, updatedAt: now, pinned: false, category: selectedCategory, messages: [userMessage, pending] }, ...current])
      setActiveId(conversationId)
    } else {
      updateConversation(conversationId, (conversation) => ({ ...conversation, updatedAt: now, category: selectedCategory, messages: [...conversation.messages, userMessage, pending] }))
    }
    const controller = new AbortController()
    abortRef.current = controller
    try {
      try {
        await streamResponse(
          { question: clean, category: selectedCategory },
          {
            onStage: (stage) => setStreamStage(stage === "retrieval_complete" ? "Generating answer…" : "Reviewing relevant sources…"),
            onDelta: (text) => updateConversation(conversationId, (conversation) => ({ ...conversation, messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, content: message.content + text } : message) })),
            onSources: (sources) => updateConversation(conversationId, (conversation) => ({ ...conversation, messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, sources } : message) })),
          },
          controller.signal,
        )
      } catch (error) {
        if (error instanceof Error && error.message === "STREAMING_UNAVAILABLE") {
          const response = await fullResponseTransport.send({ question: clean, category: selectedCategory }, controller.signal)
          updateConversation(conversationId, (conversation) => ({ ...conversation, messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, content: response.answer, sources: response.sources } : message) }))
        } else {
          throw error
        }
      }
      const completedAt = new Date().toISOString()
      updateConversation(conversationId, (conversation) => ({ ...conversation, updatedAt: completedAt, messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, createdAt: completedAt, status: "complete", durationMs: Date.parse(completedAt) - Date.parse(now) } : message) }))
    } catch (error) {
      const stopped = error instanceof DOMException && error.name === "AbortError"
      updateConversation(conversationId, (conversation) => ({ ...conversation, messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, content: message.content || (stopped ? "Generation stopped." : "I could not complete this request. Your question has been preserved; please retry when the service is available."), status: "error" } : message) }))
    } finally {
      abortRef.current = null
      setIsGenerating(false)
      requestAnimationFrame(() => composerRef.current?.focus())
    }
  }

  const filtered = useMemo(
    () => conversations.filter((conversation) =>
      conversation.title.toLowerCase().includes(search.toLowerCase()),
    ),
    [conversations, search],
  )
  const groups = useMemo(() => groupConversations(filtered), [filtered])
  if (!user) return null
  const history = (
    <div className="flex h-full flex-col">
      <div className="space-y-3 border-b p-3">
        <Button className="w-full" onClick={() => { setActiveId(null); setPrompt("") }}><MessageSquarePlus />New chat</Button>
        <div className="relative"><Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search conversations" className="pl-8" /></div>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {filtered.length === 0 && (
          <div className="px-4 py-10 text-center">
            <p className="text-sm font-medium">
              {conversations.length === 0 ? "No conversations yet" : "No matching conversations"}
            </p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              {conversations.length === 0
                ? "Start a new chat to build your private local history."
                : "Try a different search phrase."}
            </p>
          </div>
        )}
        {Object.entries(groups).map(([label, items]) => items.length > 0 && (
          <div key={label} className="mb-4">
            <p className="px-2 py-1 text-xs font-medium text-muted-foreground">{label}</p>
            {items.map((conversation) => (
              <div key={conversation.id} className={cn("group flex items-center rounded-lg border border-transparent transition-colors", activeId === conversation.id && "border-primary/15 bg-primary/[0.07] text-foreground")}>
                <button className="min-w-0 flex-1 truncate rounded-lg px-2.5 py-2.5 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" title={conversation.title} onClick={() => { setActiveId(conversation.id); setHistoryOpen(false) }}>{conversation.pinned && <Pin className="mr-1 inline size-3 text-primary" />}{conversation.title}</button>
                <div className="flex opacity-100 lg:opacity-0 lg:transition-opacity lg:group-focus-within:opacity-100 lg:group-hover:opacity-100">
                  <Button size="icon-xs" className="size-8 lg:size-6" variant="ghost" aria-label={conversation.pinned ? "Unpin conversation" : "Pin conversation"} onClick={() => updateConversation(conversation.id, (item) => ({ ...item, pinned: !item.pinned }))}><Pin /></Button>
                  <Button size="icon-xs" className="size-8 lg:size-6" variant="ghost" aria-label="Rename conversation" onClick={() => renameConversation(conversation)}><Pencil /></Button>
                  <ConfirmActionDialog trigger={<Button size="icon-xs" className="size-8 lg:size-6" variant="ghost" aria-label="Delete conversation"><Trash2 /></Button>} title="Delete conversation?" description="This removes the conversation from local history." destructive confirmLabel="Delete" onConfirm={() => { setConversations((current) => current.filter((item) => item.id !== conversation.id)); if (activeId === conversation.id) setActiveId(null) }} />
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="flex h-[calc(100svh-3.5rem)] min-w-0 overflow-hidden">
      <aside aria-label="Conversation history" className="hidden w-72 shrink-0 border-r bg-card/40 lg:block">{history}</aside>
      <section aria-label="AI conversation" className="flex min-w-0 flex-1 flex-col">
        <p className="sr-only" aria-live="polite" aria-atomic="true">
          {isGenerating
            ? "CGC Knowledge AI is preparing a response."
            : active?.messages.at(-1)?.role === "assistant"
              ? "A new assistant response is available."
              : ""}
        </p>
        <header className="flex h-12 items-center gap-2 border-b px-3 lg:hidden">
          <Sheet open={historyOpen} onOpenChange={setHistoryOpen}><SheetTrigger render={<Button variant="ghost" size="icon" aria-label="Open conversation history"><Menu /></Button>} /><SheetContent side="left" className="w-[min(22rem,88vw)] p-0">{history}</SheetContent></Sheet>
          <span className="truncate text-sm font-medium">{active?.title ?? "New conversation"}</span>
        </header>
        <div className="flex-1 overflow-y-auto">
          {!active ? (
            <div className="mx-auto flex min-h-full max-w-3xl flex-col items-center justify-center px-5 py-10 text-center sm:py-14">
              <span className="flex size-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/15 to-violet-500/15 text-primary ring-1 ring-primary/15"><Bot className="size-7" /></span>
              <h1 className="mt-6 font-heading text-3xl font-semibold tracking-tight sm:text-4xl">What would you like to know?</h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">Ask questions grounded in your authorized internal documents. Every available source will be cited.</p>
              <div className="mt-8 grid w-full gap-3 sm:grid-cols-2">{suggestions.map((suggestion) => <Button key={suggestion} variant="outline" className="h-auto min-h-16 justify-start whitespace-normal border-primary/10 bg-card p-4 text-left shadow-sm hover:border-primary/25 hover:bg-primary/[0.04]" onClick={() => void send(suggestion)}><Bot className="shrink-0 text-primary" />{suggestion}</Button>)}</div>
            </div>
          ) : (
            <ol className={cn("mx-auto max-w-3xl px-4 sm:px-6", preferences.chatDensity === "compact" ? "space-y-3 py-5" : "space-y-6 py-8")}>
              {active.messages.map((message, messageIndex) => {
                const precedingUser = [...active.messages.slice(0, messageIndex)].reverse().find((item) => item.role === "user")
                return (
                <li key={message.id} className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}>
                  <article className={cn("max-w-[92%] sm:max-w-[82%]", preferences.chatDensity === "compact" ? "px-3 py-2" : "px-4 py-3", message.role === "user" ? "rounded-2xl rounded-br-md bg-primary text-primary-foreground shadow-sm" : "rounded-xl border bg-card shadow-sm")}>
                    <p className={cn("mb-2 text-[0.68rem] font-semibold uppercase tracking-wider", message.role === "user" ? "text-primary-foreground/70" : "text-primary")}>{message.role === "user" ? "You" : "CGC Knowledge AI"}</p>
                    {message.role === "assistant" ? <SafeAnswer content={message.content} /> : <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>}
                    {message.sources && message.sources.length > 0 && <div className="mt-4 border-t pt-3"><p className="mb-2 text-xs font-medium text-muted-foreground">Company sources</p><div className="flex flex-wrap gap-2">{message.sources.map((source, index) => <Button key={source.chunkId} size="sm" variant="outline" className="max-w-full border-primary/15 bg-primary/[0.03]" onClick={() => setSelectedSource({ source, citation: index + 1 })}><span className="font-semibold text-primary">[{index + 1}]</span><span className="truncate">{source.title}</span></Button>)}</div></div>}
                    {message.role === "assistant" && message.status !== "pending" && <div className="mt-3 flex items-center gap-1 border-t pt-2 text-xs text-muted-foreground">
                      <Button size="icon-xs" className="size-11 sm:size-8" variant="ghost" aria-label={`Copy assistant response ${messageIndex + 1}`} onClick={() => { void navigator.clipboard.writeText(message.content); toast.success("Response copied.") }}><Copy /></Button>
                      <Button size="icon-xs" className="size-11 sm:size-8" variant="ghost" aria-label={`Mark assistant response ${messageIndex + 1} helpful`} onClick={() => toast.success("Feedback saved locally.")}><ThumbsUp /></Button>
                      <Button size="icon-xs" className="size-11 sm:size-8" variant="ghost" aria-label={`Mark assistant response ${messageIndex + 1} not helpful`} onClick={() => toast.info("Feedback saved locally.")}><ThumbsDown /></Button>
                      {precedingUser && <Button size="icon-xs" className="size-11 sm:size-8" variant="ghost" aria-label={`Regenerate assistant response ${messageIndex + 1}`} disabled={isGenerating} onClick={() => void send(precedingUser.content)}><RefreshCw /></Button>}
                      {message.durationMs !== undefined && <span>{(message.durationMs / 1000).toFixed(1)}s</span>}
                      {message.status === "error" && <StatusBadge tone="danger">Failed</StatusBadge>}
                    </div>}
                  </article>
                </li>
              )})}
              {isGenerating && active.messages.at(-1)?.content === "" && <li className="flex items-center gap-3"><AiTypingIndicator /><span className="text-xs text-muted-foreground">{streamStage}</span></li>}
            </ol>
          )}
        </div>
        <div className="shrink-0 border-t bg-background/95 p-2 shadow-[0_-16px_40px_-32px_oklch(0.45_0.2_275/0.5)] backdrop-blur-xl sm:p-3">
          <div className="mx-auto max-w-3xl">
            <div className="grid gap-2 rounded-2xl border bg-card p-2 shadow-lg shadow-primary/5 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-end">
              <div className="grid gap-1"><span className="px-1 text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground">Knowledge scope</span><Select value={category} onValueChange={(value) => setCategory(value ?? "all")}><SelectTrigger className="w-full sm:w-40" aria-label="Knowledge category"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All knowledge</SelectItem>{categories.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}</SelectContent></Select></div>
              <Textarea ref={composerRef} value={prompt} onChange={(event) => setPrompt(event.target.value.slice(0, 2000))} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send() } }} placeholder="Ask CGC Knowledge AI…" className="min-h-11 flex-1 resize-none border-0 shadow-none focus-visible:ring-0" aria-label="Message CGC Knowledge AI" aria-describedby="chat-composer-help" />
              {isGenerating ? <Button size="icon-lg" className="justify-self-end" variant="destructive" onClick={() => abortRef.current?.abort()} aria-label="Stop generating"><Square /></Button> : <Button size="icon-lg" className="justify-self-end" disabled={!prompt.trim()} onClick={() => void send()} aria-label="Send message"><Send /></Button>}
            </div>
            <p id="chat-composer-help" className="mt-2 text-center text-[0.68rem] text-muted-foreground">Press Enter to send and Shift+Enter for a new line. Verify important information using cited company sources.</p>
          </div>
        </div>
      </section>
      <Sheet open={selectedSource !== null} onOpenChange={(open) => !open && setSelectedSource(null)}>
        <SheetContent className="w-full sm:max-w-md"><SheetHeader className="border-b"><p className="text-xs font-semibold uppercase tracking-wider text-primary">Citation {selectedSource?.citation}</p><SheetTitle>{selectedSource?.source.title ?? "Source"}</SheetTitle></SheetHeader>{selectedSource && <div className="space-y-5 px-4"><StatusBadge>{selectedSource.source.category}</StatusBadge><div><h3 className="text-sm font-medium">Supporting excerpt</h3><blockquote className="mt-2 border-l-2 border-primary bg-muted/40 p-4 text-sm leading-7 text-foreground">{selectedSource.source.excerpt}</blockquote></div><dl className="grid grid-cols-[6rem_1fr] gap-2 text-xs"><dt className="text-muted-foreground">Chunk</dt><dd>{selectedSource.source.chunkIndex}</dd><dt className="text-muted-foreground">Document ID</dt><dd className="break-all">{selectedSource.source.documentId}</dd></dl></div>}</SheetContent>
      </Sheet>
    </div>
  )
}

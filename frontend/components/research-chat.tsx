"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { apiClient } from "@/lib/api-client"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type ConversationMessage = {
  role: "user" | "assistant" | string
  content: string
  timestamp: string
  clientId?: string
}

type ConversationResponse = {
  id: string
  title: string
  status: string
  strategy_id?: string | null
  conversation_type: string
  messages: ConversationMessage[]
  created_at: string
  updated_at: string
}

type StreamChunk =
  | { type: "content"; data: string }
  | { type: "signal_created"; data: { signal_id?: string; twitter_username?: string; ticker?: string; status?: string } }
  | { type: "error"; data?: string }
  | { type: "done" }
  | { type: string; data?: unknown }

const sortByUpdated = (items: ConversationResponse[]) =>
  [...items].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())

const STREAM_CHARS_PER_TICK = 5
const STREAM_INTERVAL_MS = 40

const createClientId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

type ResearchChatProps = {
  initialConversationId?: string | null
}

export default function ResearchChat({ initialConversationId }: ResearchChatProps) {
  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [isLoadingConversation, setIsLoadingConversation] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [signalNotice, setSignalNotice] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const hasSelectedInitialConversation = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const streamControllers = useRef<Record<string, { buffer: string; timer: ReturnType<typeof setInterval> | null }>>(
    {},
  )

  const selectedConversation = conversations.find((conv) => conv.id === selectedConversationId) || null

  const updateConversationList = useCallback((conversation: ConversationResponse) => {
    setConversations((prev) => sortByUpdated([conversation, ...prev.filter((c) => c.id !== conversation.id)]))
  }, [])

  const loadConversations = useCallback(async () => {
    try {
      const data = await apiClient.get<ConversationResponse[]>("/conversations")
      const sorted = sortByUpdated(data)
      setConversations(sorted)

      if (!hasSelectedInitialConversation.current && sorted.length > 0) {
        hasSelectedInitialConversation.current = true
        const first = sorted[0]
        setSelectedConversationId(first.id)
        setMessages(first.messages || [])
      }
    } catch (err) {
      console.error("Failed to load research conversations:", err)
      setError("Unable to load your past conversations. Please try again.")
    }
  }, [])

  const fetchConversation = useCallback(
    async (conversationId: string, options: { showSpinner?: boolean } = {}) => {
      const shouldShowSpinner = options.showSpinner !== false
      if (shouldShowSpinner) {
        setIsLoadingConversation(true)
      }
      setError(null)
      try {
        const conversation = await apiClient.get<ConversationResponse>(`/conversations/${conversationId}`)
        setMessages(conversation.messages || [])
        updateConversationList(conversation)
      } catch (err) {
        console.error("Failed to fetch conversation:", err)
        setError("Could not load the selected conversation.")
      } finally {
        if (shouldShowSpinner) {
          setIsLoadingConversation(false)
        }
      }
    },
    [updateConversationList],
  )

  const handleSelectConversation = (conversationId: string) => {
    if (conversationId === selectedConversationId) return
    setSelectedConversationId(conversationId)
    setSignalNotice(null)
    fetchConversation(conversationId)
  }

  const handleDeleteClick = useCallback((conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setDeleteConfirmId(conversationId)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteConfirmId) return

    try {
      await apiClient.delete(`/conversations/${deleteConfirmId}`)
      setConversations((prev) => prev.filter((c) => c.id !== deleteConfirmId))

      if (selectedConversationId === deleteConfirmId) {
        setSelectedConversationId(null)
        setMessages([])
      }
      setDeleteConfirmId(null)
    } catch (err) {
      console.error("Failed to delete conversation:", err)
      setError("Unable to delete conversation. Please try again.")
      setDeleteConfirmId(null)
    }
  }, [deleteConfirmId, selectedConversationId])

  const handleCancelDelete = useCallback(() => {
    setDeleteConfirmId(null)
  }, [])

  const handleCreateConversation = useCallback(async () => {
    setError(null)
    try {
      const conversation = await apiClient.post<ConversationResponse>("/conversations", {
        title: `Research #${conversations.length + 1}`,
        conversation_type: "research",
      })
      hasSelectedInitialConversation.current = true
      setSelectedConversationId(conversation.id)
      setMessages(conversation.messages || [])
      setSignalNotice(null)
      updateConversationList(conversation)
      return conversation
    } catch (err) {
      console.error("Failed to create conversation:", err)
      setError("Unable to start a new conversation right now.")
      throw err
    }
  }, [conversations.length, updateConversationList])

  const ensureConversationId = useCallback(async () => {
    if (selectedConversationId) return selectedConversationId
    const conversation = await handleCreateConversation()
    return conversation.id
  }, [handleCreateConversation, selectedConversationId])

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    })
  }, [])

  const appendAnimatedChunk = useCallback(
    (clientId: string, chunk: string) => {
      if (!chunk) return
      if (!streamControllers.current[clientId]) {
        streamControllers.current[clientId] = { buffer: "", timer: null }
      }
      const controller = streamControllers.current[clientId]
      controller.buffer += chunk

      if (controller.timer) return

      controller.timer = setInterval(() => {
        if (!controller.buffer.length) {
          if (controller.timer) {
            clearInterval(controller.timer)
            controller.timer = null
          }
          return
        }

        const nextChunk = controller.buffer.slice(0, STREAM_CHARS_PER_TICK)
        controller.buffer = controller.buffer.slice(STREAM_CHARS_PER_TICK)

        setMessages((prev) =>
          prev.map((msg) => (msg.clientId === clientId ? { ...msg, content: msg.content + nextChunk } : msg)),
        )
        scrollToBottom()

        if (!controller.buffer.length && controller.timer) {
          clearInterval(controller.timer)
          controller.timer = null
        }
      }, STREAM_INTERVAL_MS)
    },
    [scrollToBottom],
  )

  const finalizeStreamController = useCallback((clientId: string) => {
    const controller = streamControllers.current[clientId]
    if (!controller) return
    if (controller.timer) {
      clearInterval(controller.timer)
      controller.timer = null
    }
    if (controller.buffer.length) {
      const remaining = controller.buffer
      controller.buffer = ""
      setMessages((prev) =>
        prev.map((msg) => (msg.clientId === clientId ? { ...msg, content: msg.content + remaining } : msg)),
      )
    }
    delete streamControllers.current[clientId]
  }, [])

  const streamChat = useCallback(
    async (
      conversationId: string,
      message: string,
      options?: { onContentChunk?: (chunk: string) => void },
    ) => {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message }),
      })

      if (!response.ok || !response.body) {
        throw new Error("Research chat service is unavailable. Please try again.")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder("utf-8")
      let buffer = ""
      let assistantText = ""

      const processLine = (line: string) => {
        if (!line) return
        try {
          const payload = JSON.parse(line) as StreamChunk

          if (payload.type === "content") {
            const contentData = payload.data as string
            if (contentData) {
              assistantText += contentData
              options?.onContentChunk?.(contentData)
            }
          } else if (payload.type === "signal_created") {
            const signalData = payload.data as { signal_id?: string; twitter_username?: string; ticker?: string; status?: string }
            setSignalNotice(`Signal created: Monitoring @${signalData?.twitter_username}${signalData?.ticker ? ` for $${signalData.ticker}` : ''}`)
          } else if (payload.type === "error") {
            const errorData = payload.data as string | undefined
            throw new Error(errorData || "Chat error")
          }
        } catch (err) {
          console.error("Failed to parse stream chunk:", err)
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split("\n")
        buffer = parts.pop() || ""
        parts.filter((part) => part.trim().length > 0).forEach((part) => processLine(part.trim()))
      }

      if (buffer.trim()) {
        processLine(buffer.trim())
      }

      return assistantText
    },
    [],
  )

  const handleSendMessage = async (event?: React.FormEvent) => {
    event?.preventDefault()
    if (!input.trim()) return

    setError(null)
    const messageContent = input.trim()
    setInput("")
    const conversationId = await ensureConversationId()

    const userMessage: ConversationMessage = {
      role: "user",
      content: messageContent,
      timestamp: new Date().toISOString(),
    }
    const assistantClientId = createClientId()
    const assistantPlaceholder: ConversationMessage = {
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      clientId: assistantClientId,
    }
    setMessages((prev) => [...prev, userMessage, assistantPlaceholder])
    setIsSending(true)

    try {
      const assistantResponse = await streamChat(conversationId, messageContent, {
        onContentChunk: (chunk) => appendAnimatedChunk(assistantClientId, chunk),
      })
      finalizeStreamController(assistantClientId)

      if (!assistantResponse) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.clientId === assistantClientId
              ? { ...msg, content: "No response received. Please try again." }
              : msg,
          ),
        )
      }
      await fetchConversation(conversationId, { showSpinner: false })
    } catch (err) {
      console.error("Chat failed:", err)
      setError(err instanceof Error ? err.message : "Unable to process your request.")
      setMessages((prev) =>
        prev.map((msg) =>
          msg.clientId === assistantClientId
            ? { ...msg, content: "There was an error generating a response." }
            : msg,
        ),
      )
      finalizeStreamController(assistantClientId)
    } finally {
      setIsSending(false)
    }
  }

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  useEffect(() => {
    if (!initialConversationId) return
    const focusConversation = async () => {
      try {
        setSelectedConversationId(initialConversationId)
        await fetchConversation(initialConversationId)
        hasSelectedInitialConversation.current = true
      } catch (err) {
        console.error("Failed to focus conversation:", err)
        setError("This conversation no longer exists. It may have been deleted.")
      }
    }
    focusConversation()
  }, [fetchConversation, initialConversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    return () => {
      Object.entries(streamControllers.current).forEach(([, controller]) => {
        if (controller.timer) clearInterval(controller.timer)
      })
      streamControllers.current = {}
    }
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-[#050608] text-white">
      {/* Sidebar */}
      <aside className={`relative flex w-72 h-screen flex-col border-r border-white/10 bg-[#0a0b0f] transition-all duration-300 flex-shrink-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {/* Sidebar Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-10 top-24 z-50 rounded-r-lg bg-white/10 p-2 text-white hover:bg-white/20 transition-all duration-300"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 transition-transform duration-300"
            style={{ transform: sidebarOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <div className="flex items-center justify-between px-5 py-5 border-b border-white/10 flex-shrink-0">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-white/40">Research Lab</p>
            <h2 className="text-lg font-semibold">AI Research</h2>
          </div>
          <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/70">Beta</span>
        </div>

        <div className="px-5 py-4 flex-shrink-0">
          <Button
            className="w-full justify-between rounded-2xl bg-white/10 text-white hover:bg-white/20"
            onClick={handleCreateConversation}
            disabled={isSending}
          >
            <span>New research chat</span>
            <span className="text-lg">+</span>
          </Button>
          <p className="mt-3 text-xs text-white/40">All research chats auto-save in this panel.</p>
        </div>

        {/* Sidebar scrollable area */}
        <div className="flex-1 min-h-0 overflow-y-auto px-3 pb-6 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {/* Research Conversations Section */}
          <div className="space-y-2 mb-6">
            <div className="px-2 py-2 text-xs uppercase tracking-wide text-white/40">
              Research
            </div>
            {conversations.filter(c => c.conversation_type === "research").length === 0 && (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-center text-xs text-white/50">
                No research chats yet.
              </div>
            )}
            {conversations.filter(c => c.conversation_type === "research").map((conversation) => (
              <div
                key={conversation.id}
                className="relative group"
              >
                <button
                  onClick={() => handleSelectConversation(conversation.id)}
                  className={cn(
                    "w-full rounded-2xl border px-4 py-3 text-left transition",
                    conversation.id === selectedConversationId
                      ? "border-white/30 bg-white/10"
                      : "border-white/5 hover:border-white/20",
                  )}
                >
                  <div className="flex items-center justify-between text-sm font-medium pr-8">
                    <span className="truncate">{conversation.title}</span>
                  </div>
                  <p className="text-[11px] text-white/50">
                    {new Date(conversation.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </button>
                {/* Delete button */}
                <button
                  onClick={(e) => handleDeleteClick(conversation.id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-destructive/80 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-destructive z-10"
                  title="Delete conversation"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          {/* Strategy Conversations Section */}
          {conversations.filter(c => c.conversation_type === "strategy").length > 0 && (
            <div className="space-y-2 mb-6 pt-4 border-t border-white/10">
              <div className="px-2 py-2 text-xs uppercase tracking-wide text-white/40">
                Strategy
              </div>
              {conversations.filter(c => c.conversation_type === "strategy").map((conversation) => (
                <div
                  key={conversation.id}
                  className="relative group"
                >
                  <Link href={`/chat?conversationId=${conversation.id}`}>
                    <button
                      className={cn(
                        "w-full rounded-2xl border px-4 py-3 text-left transition",
                        "border-white/5 hover:border-white/20",
                      )}
                    >
                      <div className="flex items-center justify-between text-sm font-medium pr-8">
                        <span className="truncate">{conversation.title}</span>
                        {conversation.strategy_id && (
                          <span className="text-[10px] uppercase tracking-wide text-secondary">linked</span>
                        )}
                      </div>
                      <p className="text-[11px] text-white/50">
                        {new Date(conversation.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </button>
                  </Link>
                  {/* Delete button */}
                  <button
                    onClick={(e) => handleDeleteClick(conversation.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-destructive/80 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-destructive z-10"
                    title="Delete conversation"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-white/10 px-5 py-4 text-xs text-white/40 flex-shrink-0">
          Powered by web search & Twitter intelligence
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-1 flex-col h-screen overflow-hidden">
        {/* Fixed header */}
        <header className="flex items-center justify-between border-b border-white/10 px-8 py-5 flex-shrink-0">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/30">Research workspace</p>
            <h1 className="text-2xl font-semibold">{selectedConversation?.title ?? "What would you like to research?"}</h1>
          </div>
          {selectedConversation?.status && (
            <span className="rounded-full border border-white/20 px-4 py-1 text-xs uppercase tracking-wide text-white/60">
              {selectedConversation.status}
            </span>
          )}
        </header>

        {signalNotice && (
          <div className="mx-8 mt-4 rounded-2xl border border-green-500/40 bg-green-500/10 px-4 py-3 text-sm text-white flex-shrink-0">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>{signalNotice}</span>
              <Button size="sm" variant="ghost" onClick={() => setSignalNotice(null)}>
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {/* Chat messages scrollable area */}
        <div className="flex-1 min-h-0 overflow-y-auto px-8 py-6 space-y-6 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {!selectedConversation ? (
            <div className="flex h-full items-center justify-center rounded-3xl border border-dashed border-white/10 bg-white/5 p-16 text-center">
              <div>
                <p className="text-xl font-semibold">New research chat</p>
                <p className="text-sm text-white/50">
                  Ask about markets, analyze Twitter sentiment, track influencers, or research any topic.
                </p>
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-secondary text-sm font-semibold mb-2">Web Research</div>
                    <p className="text-xs text-white/60">Search the web for current information, news, and market data</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-secondary text-sm font-semibold mb-2">Twitter Intelligence</div>
                    <p className="text-xs text-white/60">Find viral tweets, analyze accounts, track hashtags & sentiment</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-secondary text-sm font-semibold mb-2">Market Analysis</div>
                    <p className="text-xs text-white/60">Research stocks, crypto, and financial markets in real-time</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-secondary text-sm font-semibold mb-2">Signal Creation</div>
                    <p className="text-xs text-white/60">Set up automated Twitter monitoring for trading signals</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              {isLoadingConversation ? (
                <div className="rounded-3xl border border-white/10 bg-white/5 px-6 py-10 text-center text-sm text-white/60">
                  Loading conversation...
                </div>
              ) : messages.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-white/10 px-6 py-12 text-center text-white/50">
                  Start your research by asking a question or requesting analysis.
                </div>
              ) : (
                messages.map((message, idx) => {
                  const isStreaming = message.role === "assistant" && message.clientId && streamControllers.current[message.clientId]?.buffer
                  return (
                    <div
                      key={message.clientId ?? `${message.timestamp}-${idx}`}
                      className={cn(
                        "w-full max-w-3xl rounded-3xl border px-6 py-4 shadow transition",
                        message.role === "user"
                          ? "ml-auto border-white/10 bg-[#1b1d24]"
                          : "mr-auto border-white/5 bg-[#0d0f15]",
                      )}
                    >
                      <div className="mb-2 flex items-center gap-3 text-xs uppercase tracking-wide text-white/40">
                        <span>{message.role === "user" ? "You" : "Research AI"}</span>
                        <span className="text-white/30">-</span>
                        <span>
                          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        {isStreaming && (
                          <span className="ml-2 text-secondary animate-pulse">●</span>
                        )}
                      </div>
                      {message.role === "assistant" ? (
                        <div className="prose prose-invert max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h2: ({node, ...props}) => <h2 className="text-xl font-bold text-white mt-6 mb-3" {...props} />,
                              h3: ({node, ...props}) => <h3 className="text-lg font-semibold text-white mt-4 mb-2" {...props} />,
                              p: ({node, ...props}) => <p className="text-white/90 leading-relaxed mb-4" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc list-inside text-white/90 space-y-2 mb-4" {...props} />,
                              ol: ({node, ...props}) => <ol className="list-decimal list-inside text-white/90 space-y-2 mb-4" {...props} />,
                              li: ({node, ...props}) => <li className="text-white/90" {...props} />,
                              a: ({node, ...props}) => <a className="text-secondary hover:text-secondary/80 underline" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                              code: ({node, ...props}) => <code className="bg-white/10 px-2 py-1 rounded text-secondary font-mono text-sm" {...props} />,
                              hr: ({node, ...props}) => <hr className="border-white/20 my-6" {...props} />,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                          {isStreaming && (
                            <span className="inline-block w-2 h-4 ml-1 bg-secondary animate-pulse" />
                          )}
                        </div>
                      ) : (
                        <div className="prose prose-invert max-w-none leading-relaxed text-white/90">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                              strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                              em: ({ children }) => <em className="italic text-white/95">{children}</em>,
                              h1: ({ children }) => <h1 className="text-2xl font-bold text-white mb-3 mt-4">{children}</h1>,
                              h2: ({ children }) => <h2 className="text-xl font-bold text-white mb-2 mt-3">{children}</h2>,
                              h3: ({ children }) => <h3 className="text-lg font-bold text-white mb-2 mt-3">{children}</h3>,
                              ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                              li: ({ children }) => <li className="mb-1">{children}</li>,
                              code: ({ children }) => <code className="bg-white/10 px-1.5 py-0.5 rounded text-secondary">{children}</code>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )
                })
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Fixed input form at bottom */}
        <form onSubmit={handleSendMessage} className="border-t border-white/10 px-8 pb-8 pt-4 flex-shrink-0 bg-[#050608]">
          {error && (
            <div className="mb-3 rounded-2xl border border-destructive/60 bg-destructive/10 px-4 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="rounded-3xl border border-white/10 bg-[#0d0f15] p-4 shadow-inner">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder="Ask me to research anything... market analysis, Twitter sentiment, viral content, etc."
              rows={3}
              className="w-full resize-none bg-transparent text-base text-white/90 outline-none placeholder:text-white/40"
            />
            <div className="mt-3 flex items-center justify-between text-xs text-white/40">
              <span>Shift + Enter for newline</span>
              <Button
                type="submit"
                disabled={isSending || !input.trim()}
                className="rounded-full bg-secondary px-6 text-black hover:bg-secondary/90 disabled:opacity-50"
              >
                {isSending ? "Researching..." : messages.length === 0 ? "Start research" : "Send"}
              </Button>
            </div>
          </div>
        </form>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={handleCancelDelete}>
          <div
            className="w-full max-w-md rounded-3xl border border-white/20 bg-[#0a0b0f] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-white">Delete Conversation</h3>
              <p className="mt-2 text-sm text-white/60">
                Are you sure you want to delete this research conversation? This action cannot be undone.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleCancelDelete}
                variant="outline"
                className="flex-1 rounded-xl border-white/20 hover:bg-white/10"
                style={{ color: "black" }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmDelete}
                className="flex-1 rounded-xl bg-destructive text-white hover:bg-destructive/90"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

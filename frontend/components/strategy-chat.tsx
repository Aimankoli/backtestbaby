"use client"

import { ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react"
import { createPortal } from "react-dom"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { apiClient } from "@/lib/api-client"
import { cn } from "@/lib/utils"
import SignalEventDetail from "@/components/signal-event-detail"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type StrategyChatProps = {
  initialStrategyId?: string | null
}

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
  messages: ConversationMessage[]
  created_at: string
  updated_at: string
}

type StrategyBacktestResult = {
  backtest_id?: string
  metrics?: Record<string, number | string>
  plot_path?: string | null
  plot_html?: string | null
  data_csv?: string | null
  script_path?: string | null
  ran_at?: string
}

type StrategyResponse = {
  id: string
  conversation_id: string
  user_id: string
  name: string
  description?: string | null
  status: string
  backtest_code?: string | null
  backtest_results: StrategyBacktestResult[]
  created_at: string
  updated_at: string
}

type BacktestPayload = {
  backtest_id?: string
  metrics?: Record<string, number | string>
  plot_path?: string | null
  plot_html?: string | null
  data_csv?: string | null
  code?: string | null
  description?: string | null
  script_path?: string | null
}

type ToolEvent = {
  tool_name?: string
  status?: string
  input?: any
  output?: any
  error?: string
  [key: string]: any
}

type StreamChunk =
  | { type: "content"; data: string }
  | { type: "backtest_result"; data: BacktestPayload }
  | { type: "strategy_created"; data: { strategy_id?: string; name?: string } }
  | { type: "signal_created"; data: { signal_id?: string; twitter_username?: string; ticker?: string; status?: string } }
  | { type: "tool_event"; data: ToolEvent }
  | { type: "error"; data?: string }
  | { type: "done" }
  | { type: string; data?: unknown }

const sortByUpdated = (items: ConversationResponse[]) =>
  [...items].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())

const numberFromMetric = (value?: number | string) => {
  if (typeof value === "number") return value
  if (typeof value === "string") {
    const parsed = Number(value.replace(/%/g, ""))
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const formatPercent = (value?: number | string) => {
  const parsed = numberFromMetric(value)
  return typeof parsed === "number" ? `${parsed.toFixed(2)}%` : "--"
}

const formatRatio = (value?: number | string) => {
  const parsed = numberFromMetric(value)
  return typeof parsed === "number" ? parsed.toFixed(2) : "--"
}

const STREAM_CHARS_PER_TICK = 5
const STREAM_INTERVAL_MS = 40

const createClientId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export default function StrategyChat({ initialStrategyId }: StrategyChatProps) {
  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [isLoadingConversation, setIsLoadingConversation] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [strategyNotice, setStrategyNotice] = useState<string | null>(null)
  const [signalNotice, setSignalNotice] = useState<string | null>(null)
  const [backtestResult, setBacktestResult] = useState<BacktestPayload | null>(null)
  const [strategyInfo, setStrategyInfo] = useState<StrategyResponse | null>(null)
  const [signals, setSignals] = useState<Array<{id: string, twitter_username: string, ticker?: string, status: string}>>([])
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [deleteSignalConfirmId, setDeleteSignalConfirmId] = useState<string | null>(null)
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([])
  const [isProcessingTools, setIsProcessingTools] = useState(false)
  const hasSelectedInitialConversation = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const streamControllers = useRef<Record<string, { buffer: string; timer: ReturnType<typeof setInterval> | null }>>(
    {},
  )

  const selectedConversation = useMemo(
    () => conversations.find((conv) => conv.id === selectedConversationId) || null,
    [conversations, selectedConversationId],
  )

  const updateConversationList = useCallback((conversation: ConversationResponse) => {
    setConversations((prev) => sortByUpdated([conversation, ...prev.filter((c) => c.id !== conversation.id)]))
  }, [])

  const loadStrategyDetails = useCallback(async (strategyId: string) => {
    try {
      const strategy = await apiClient.get<StrategyResponse>(`/strategies/${strategyId}`)
      setStrategyInfo(strategy)
      const latestBacktest =
        strategy.backtest_results?.[strategy.backtest_results.length - 1] ?? null
      setBacktestResult(
        latestBacktest
          ? {
              backtest_id: latestBacktest.backtest_id,
              metrics: latestBacktest.metrics ?? {},
              plot_path: latestBacktest.plot_path,
              plot_html: latestBacktest.plot_html,
              data_csv: latestBacktest.data_csv,
              script_path: latestBacktest.script_path,
            }
          : null,
      )
    } catch (err) {
      console.error("Failed to load strategy details:", err)
    }
  }, [])

  const loadSignals = useCallback(async () => {
    try {
      const data = await apiClient.get<Array<{id: string, twitter_username: string, ticker?: string, status: string}>>("/signals")
      setSignals(data)
    } catch (err) {
      console.error("Failed to load signals:", err)
    }
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
        if (first.strategy_id) {
          await loadStrategyDetails(first.strategy_id)
        } else {
          setStrategyInfo(null)
          setBacktestResult(null)
        }
      }
    } catch (err) {
      console.error("Failed to load conversations:", err)
      setError("Unable to load your past conversations. Please try again.")
    }
  }, [loadStrategyDetails])

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

        if (conversation.strategy_id) {
          await loadStrategyDetails(conversation.strategy_id)
        } else {
          setStrategyInfo(null)
          setBacktestResult(null)
        }
      } catch (err) {
        console.error("Failed to fetch conversation:", err)
        setError("Could not load the selected conversation.")
      } finally {
        if (shouldShowSpinner) {
          setIsLoadingConversation(false)
        }
      }
    },
    [loadStrategyDetails, updateConversationList],
  )

  const handleSelectConversation = (conversationId: string) => {
    if (conversationId === selectedConversationId) return
    setSelectedConversationId(conversationId)
    setStrategyNotice(null)
    fetchConversation(conversationId)
  }

  const handleDeleteClick = useCallback((conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent selecting the conversation when clicking delete
    setDeleteConfirmId(conversationId)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteConfirmId) return

    try {
      // Find the conversation to get its strategy_id
      const conversation = conversations.find((c) => c.id === deleteConfirmId)

      // Delete the conversation
      await apiClient.delete(`/conversations/${deleteConfirmId}`)

      // Also delete the associated strategy if it exists
      if (conversation?.strategy_id) {
        try {
          await apiClient.delete(`/strategies/${conversation.strategy_id}`)
        } catch (strategyErr) {
          console.error("Failed to delete associated strategy:", strategyErr)
          // Continue even if strategy deletion fails
        }
      }

      setConversations((prev) => prev.filter((c) => c.id !== deleteConfirmId))

      // If the deleted conversation was selected, clear the selection
      if (selectedConversationId === deleteConfirmId) {
        setSelectedConversationId(null)
        setMessages([])
        setStrategyInfo(null)
        setBacktestResult(null)
      }
      setDeleteConfirmId(null)
    } catch (err) {
      console.error("Failed to delete conversation:", err)
      setError("Unable to delete conversation. Please try again.")
      setDeleteConfirmId(null)
    }
  }, [deleteConfirmId, selectedConversationId, conversations])

  const handleCancelDelete = useCallback(() => {
    setDeleteConfirmId(null)
  }, [])

  const handleDeleteSignalClick = useCallback((signalId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setDeleteSignalConfirmId(signalId)
  }, [])

  const handleConfirmSignalDelete = useCallback(async () => {
    if (!deleteSignalConfirmId) return

    try {
      // Find the signal (we'd need to fetch full signal data to get conversation_id)
      // For now, just delete the signal
      await apiClient.delete(`/signals/${deleteSignalConfirmId}`)

      // Remove from local state
      setSignals((prev) => prev.filter((s) => s.id !== deleteSignalConfirmId))

      // Clear selection if this signal was selected
      if (selectedSignalId === deleteSignalConfirmId) {
        setSelectedSignalId(null)
      }

      setDeleteSignalConfirmId(null)
    } catch (err) {
      console.error("Failed to delete signal:", err)
      setError("Unable to delete signal. Please try again.")
      setDeleteSignalConfirmId(null)
    }
  }, [deleteSignalConfirmId, selectedSignalId])

  const handleCancelSignalDelete = useCallback(() => {
    setDeleteSignalConfirmId(null)
  }, [])

  const handleCreateConversation = useCallback(async () => {
    setError(null)
    try {
      const conversation = await apiClient.post<ConversationResponse>("/conversations", {
        title: `Chat Session #${conversations.length + 1}`,
      })
      hasSelectedInitialConversation.current = true
      setSelectedConversationId(conversation.id)
      setMessages(conversation.messages || [])
      setStrategyInfo(null)
      setBacktestResult(null)
      setStrategyNotice(null)
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
        throw new Error("Chat service is unavailable. Please try again.")
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
          } else if (payload.type === "backtest_result") {
            const backtestData = payload.data as BacktestPayload
            setBacktestResult(backtestData || null)
          } else if (payload.type === "strategy_created") {
            const strategyData = payload.data as { strategy_id?: string; name?: string }
            setStrategyNotice(`Strategy "${strategyData?.name ?? "Untitled"}" saved to your library.`)
            if (strategyData?.strategy_id) {
              loadStrategyDetails(strategyData.strategy_id).catch(() => undefined)
            }
          } else if (payload.type === "signal_created") {
            const signalData = payload.data as { signal_id?: string; twitter_username?: string; ticker?: string; status?: string }
            setSignalNotice(`Signal created: Monitoring @${signalData?.twitter_username}${signalData?.ticker ? ` for $${signalData.ticker}` : ''}`)
            if (signalData?.signal_id) {
              setSignals((prev) => [...prev, {
                id: signalData.signal_id!,
                twitter_username: signalData.twitter_username || 'unknown',
                ticker: signalData.ticker,
                status: signalData.status || 'active'
              }])
            }
          } else if (payload.type === "tool_event") {
            const toolEvent = payload.data as ToolEvent
            console.log('[TOOL_EVENT]', toolEvent)
            setToolEvents((prev) => [...prev, toolEvent])
            setIsProcessingTools(true)
          } else if (payload.type === "done") {
            setIsProcessingTools(false)
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
    [loadStrategyDetails],
  )

  const handleSendMessage = async (event?: React.FormEvent) => {
    event?.preventDefault()
    if (!input.trim()) return

    setError(null)
    const messageContent = input.trim()
    setInput("")
    setToolEvents([])  // Clear previous tool events
    setIsProcessingTools(false)
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
    if (initialStrategyId) {
      hasSelectedInitialConversation.current = true
    }
  }, [initialStrategyId])

  useEffect(() => {
    loadConversations()
    loadSignals()
  }, [loadConversations, loadSignals])

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

  useEffect(() => {
    if (!initialStrategyId) return
    const focusStrategyConversation = async () => {
      try {
        const strategy = await apiClient.get<StrategyResponse>(`/strategies/${initialStrategyId}`)
        if (strategy.conversation_id) {
          setSelectedConversationId(strategy.conversation_id)
          await fetchConversation(strategy.conversation_id)
        }
      } catch (err) {
        console.error("Failed to focus strategy conversation:", err)
        // If strategy doesn't exist (404), show error and clear the strategyId from URL
        setError("This strategy no longer exists. It may have been deleted.")
        // Clear the URL parameter
        if (typeof window !== 'undefined') {
          const url = new URL(window.location.href)
          url.searchParams.delete('strategyId')
          window.history.replaceState({}, '', url)
        }
      }
    }
    focusStrategyConversation()
  }, [fetchConversation, initialStrategyId])

  const metrics = (backtestResult?.metrics ?? {}) as Record<string, number | string>

  return (
    <div className="flex h-screen overflow-hidden bg-[#050608] text-white">
      {/* Sidebar with its own scroll */}
      <aside className={`relative flex w-72 h-screen flex-col border-r border-white/10 bg-[#0a0b0f] transition-all duration-300 flex-shrink-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {/* Sidebar Toggle Button attached to sidebar */}
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
            <p className="text-xs uppercase tracking-[0.2em] text-white/40">Backtest Lab</p>
            <h2 className="text-lg font-semibold">Strategy Studio</h2>
          </div>
          <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/70">Beta</span>
        </div>
        <div className="px-5 py-4 flex-shrink-0">
          <Button
            className="w-full justify-between rounded-2xl bg-white/10 text-white hover:bg-white/20"
            onClick={handleCreateConversation}
            disabled={isSending}
          >
            <span>New Chat</span>
            <span className="text-lg">+</span>
          </Button>
          <p className="mt-3 text-xs text-white/40">All drafts auto-save in this panel.</p>
        </div>
        {/* Sidebar scrollable area */}
        <div className="flex-1 min-h-0 overflow-y-auto px-3 pb-6 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {/* Conversations Section */}
          <div className="space-y-2 mb-6">
            <div className="px-2 py-2 text-xs uppercase tracking-wide text-white/40">
              Conversations
            </div>
            {conversations.length === 0 && (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-center text-xs text-white/50">
                No conversations yet. Create your first strategy to get started.
              </div>
            )}
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
              className="relative group"
            >
              <button
                  onClick={() => {
                  handleSelectConversation(conversation.id)
                  setSelectedSignalId(null)
                }}
                  className={cn(
                    "w-full rounded-2xl border px-4 py-3 text-left transition",
                    conversation.id === selectedConversationId && !selectedSignalId
                      ? "border-white/30 bg-white/10"
                      : "border-white/5 hover:border-white/20",
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
              {/* Delete button with animation */}
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

          {/* Signals Section */}
          {signals.length > 0 && (
            <div className="space-y-2 pt-4 border-t border-white/10">
              <div className="px-2 py-2 text-xs uppercase tracking-wide text-white/40">
                Active Signals
              </div>
              {signals.map((signal) => (
                <div
                  key={signal.id}
                  className="relative group"
                >
                  <button
                    onClick={() => setSelectedSignalId(signal.id)}
                    className={cn(
                      "w-full rounded-2xl border px-4 py-3 text-left transition",
                      selectedSignalId === signal.id
                        ? "border-green-500/40 bg-green-500/10"
                        : "border-white/5 hover:border-white/20",
                    )}
                  >
                    <div className="flex items-center justify-between text-sm font-medium pr-8">
                      <span className="truncate">@{signal.twitter_username}</span>
                      <span className={cn(
                        "text-[10px] uppercase tracking-wide rounded-full px-2 py-0.5",
                        signal.status === 'active' ? "bg-green-500/20 text-green-400" : "bg-gray-500/20 text-gray-400"
                      )}>
                        {signal.status}
                      </span>
                    </div>
                    {signal.ticker && (
                      <p className="text-[11px] text-white/50 font-mono">
                        ${signal.ticker}
                      </p>
                    )}
                  </button>
                  {/* Delete button with animation */}
                  <button
                    onClick={(e) => handleDeleteSignalClick(signal.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-destructive/80 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-destructive z-10"
                    title="Delete signal"
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
          Need historical runs?{" "}
          <Link href="/strategies" className="text-secondary">
            View strategies {'->'}
          </Link>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-1 flex-col h-screen overflow-hidden">
        {/* Fixed header */}
        <header className="flex items-center justify-between border-b border-white/10 px-8 py-5 flex-shrink-0">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/30">Chat workspace</p>
            <h1 className="text-2xl font-semibold">{selectedConversation?.title ?? "What's on the agenda today?"}</h1>
          </div>
          {selectedConversation?.status && (
            <span className="rounded-full border border-white/20 px-4 py-1 text-xs uppercase tracking-wide text-white/60">
              {selectedConversation.status}
            </span>
          )}
        </header>

        {strategyNotice && (
          <div className="mx-8 mt-4 rounded-2xl border border-secondary/40 bg-secondary/10 px-4 py-3 text-sm text-white flex-shrink-0">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>{strategyNotice}</span>
              <div className="flex gap-2">
                <Link href="/strategies">
                  <Button size="sm" className="bg-secondary text-black hover:bg-secondary/80">
                    View strategies
                  </Button>
                </Link>
                <Button size="sm" variant="ghost" onClick={() => setStrategyNotice(null)}>
                  Dismiss
                </Button>
              </div>
            </div>
          </div>
        )}

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

        {/* Chat messages scrollable area - THE ONLY main scroll bar */}
        <div className="flex-1 min-h-0 overflow-y-auto px-8 py-6 space-y-6 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {selectedSignalId ? (
            <SignalEventDetail signalId={selectedSignalId} />
          ) : !selectedConversation ? (
            <div className="flex h-full items-center justify-center rounded-3xl border border-dashed border-white/10 bg-white/5 p-16 text-center">
              <div>
                <p className="text-xl font-semibold">New strategy</p>
                <p className="text-sm text-white/50">
                  Describe the setup you want to trade and we&apos;ll fetch the data, build the code, and run the backtest.
                </p>
              </div>
            </div>
          ) : (
            <>
              {strategyInfo && (
                <BacktestInsight strategy={strategyInfo} backtest={backtestResult} metrics={metrics} />
              )}

              {/* Tool Progress Display */}
              {toolEvents.length > 0 && (
                <div className="rounded-3xl border border-secondary/40 bg-gradient-to-br from-secondary/10 via-transparent to-black/20 p-6 shadow-xl">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center",
                      isProcessingTools ? "bg-secondary animate-pulse" : "bg-green-500"
                    )}>
                      {isProcessingTools ? (
                        <svg className="w-5 h-5 text-black animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.4em] text-white/40">Tool Execution</p>
                      <h3 className="text-lg font-semibold text-white">
                        {isProcessingTools ? "Processing backtest tools..." : "Tools completed"}
                      </h3>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {toolEvents.map((event, idx) => {
                      const toolName = event.tool_name || event.name || `Tool ${idx + 1}`
                      const isComplete = event.status === 'complete' || event.status === 'success'
                      const isError = event.status === 'error' || event.status === 'failed'
                      const isRunning = event.status === 'running' || event.status === 'executing'

                      return (
                        <div
                          key={idx}
                          className={cn(
                            "flex items-center gap-3 px-4 py-3 rounded-2xl border transition-all",
                            isComplete ? "border-green-500/30 bg-green-500/10" :
                            isError ? "border-red-500/30 bg-red-500/10" :
                            isRunning ? "border-secondary/30 bg-secondary/10 animate-pulse" :
                            "border-white/10 bg-white/5"
                          )}
                        >
                          <div className={cn(
                            "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center",
                            isComplete ? "bg-green-500" :
                            isError ? "bg-red-500" :
                            isRunning ? "bg-secondary animate-pulse" :
                            "bg-white/20"
                          )}>
                            {isComplete ? (
                              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                              </svg>
                            ) : isError ? (
                              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            ) : isRunning ? (
                              <div className="w-2 h-2 bg-black rounded-full animate-ping" />
                            ) : (
                              <div className="w-2 h-2 bg-white/50 rounded-full" />
                            )}
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{toolName}</p>
                            {event.output && typeof event.output === 'string' && (
                              <p className="text-xs text-white/50 mt-1 truncate">{event.output}</p>
                            )}
                            {event.error && (
                              <p className="text-xs text-red-400 mt-1">{event.error}</p>
                            )}
                          </div>
                          {isRunning && (
                            <div className="flex-shrink-0">
                              <svg className="w-5 h-5 text-secondary animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                              </svg>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {isLoadingConversation ? (
                <div className="rounded-3xl border border-white/10 bg-white/5 px-6 py-10 text-center text-sm text-white/60">
                  Loading conversation...
                </div>
              ) : messages.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-white/10 px-6 py-12 text-center text-white/50">
                  Share your first strategy prompt to kick off the analysis.
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
                        <span>{message.role === "user" ? "You" : "Strategy Copilot"}</span>
                        <span className="text-white/30">-</span>
                        <span>
                          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        {isStreaming && (
                          <span className="ml-2 text-secondary animate-pulse">●</span>
                        )}
                      </div>
                      <p className="whitespace-pre-wrap leading-relaxed text-white/90">
                        {message.content}
                        {isStreaming && (
                          <span className="inline-block w-2 h-4 ml-1 bg-secondary animate-pulse" />
                        )}
                      </p>
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
              placeholder="Ask anything... share indicators, entry rules, or constraints"
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
                {isSending ? "Thinking..." : messages.length === 0 ? "Backtest strategy" : "Send"}
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
                Are you sure you want to delete this conversation? This action cannot be undone.
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

      {/* Signal Delete Confirmation Modal */}
      {deleteSignalConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={handleCancelSignalDelete}>
          <div
            className="w-full max-w-md rounded-3xl border border-white/20 bg-[#0a0b0f] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-white">Delete Signal</h3>
              <p className="mt-2 text-sm text-white/60">
                Are you sure you want to delete this signal? This action cannot be undone.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleCancelSignalDelete}
                variant="outline"
                className="flex-1 rounded-xl border-white/20 hover:bg-white/10"
                style={{ color: "black" }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmSignalDelete}
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

type ModalCardProps = {
  title: string
  subtitle: string
  onClick: () => void
  children: ReactNode
}

function ModalCard({ title, subtitle, onClick, children }: ModalCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group h-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-white/40"
    >
      <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-wide text-white/40">
        <span>{subtitle}</span>
        <span className="rounded-full border border-white/20 px-2 py-0.5 text-[10px] text-white/60">Expand</span>
      </div>
      <h4 className="mb-3 text-lg font-semibold text-white">{title}</h4>
      <div className="text-sm text-white/80">{children}</div>
    </button>
  )
}

type InsightModalProps = {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

function InsightModal({ open, onClose, title, children }: InsightModalProps) {
  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={onClose}>
      <div
        className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-white/20 bg-[#050608] p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">Expanded view</p>
            <h3 className="text-2xl font-semibold text-white">{title}</h3>
          </div>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  )
}

type BacktestInsightProps = {
  strategy: StrategyResponse | null
  backtest: BacktestPayload | null
  metrics: Record<string, number | string>
}

function BacktestInsight({ strategy, backtest, metrics }: BacktestInsightProps) {
  const [activeModal, setActiveModal] = useState<"code" | "chart" | "metrics" | null>(null)

  // Get data directly from strategy (already loaded from MongoDB)
  const codeContent = strategy?.backtest_code ?? null
  const plotHtml = backtest?.plot_html ?? null
  const dataCsv = backtest?.data_csv ?? null

  const hasBacktestResults = backtest && Object.keys(metrics).length > 0
  const codePreview = codeContent?.split("\n").slice(0, 6).join("\n") ?? "Click to view strategy code..."

  // Debug logging
  useEffect(() => {
    if (backtest) {
      console.log('Backtest data:', {
        hasPlotHtml: !!plotHtml,
        plotHtmlLength: plotHtml?.length,
        hasDataCsv: !!dataCsv,
        dataCsvLength: dataCsv?.length,
        hasCode: !!codeContent,
        codeLength: codeContent?.length,
        metricsCount: Object.keys(metrics).length
      })
    }
  }, [backtest, plotHtml, dataCsv, codeContent, metrics])

  const quickStats = hasBacktestResults
    ? [
        { label: "Return %", value: formatPercent(metrics["Return [%]"] ?? metrics.total_return) },
        { label: "Sharpe Ratio", value: formatRatio(metrics["Sharpe Ratio"] ?? metrics.sharpe_ratio) },
        { label: "Win Rate", value: formatPercent(metrics["Win Rate [%]"] ?? metrics.win_rate) },
        { label: "Trades", value: metrics["# Trades"] ?? metrics.num_trades ?? "--" },
      ]
    : [
        { label: "Return %", value: "Pending" },
        { label: "Sharpe Ratio", value: "Pending" },
        { label: "Win Rate", value: "Pending" },
        { label: "Trades", value: "Pending" },
      ]

  return (
    <div className="space-y-5 rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 via-transparent to-black/20 p-6 shadow-xl">
      {strategy && (
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">Strategy metadata</p>
            <h3 className="text-2xl font-semibold text-white">{strategy.name}</h3>
            {strategy.description && <p className="mt-1 text-sm text-white/60">{strategy.description}</p>}
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-white/70">
            <span className="rounded-full border border-white/20 px-4 py-1">Status - {strategy.status}</span>
            <span className="rounded-full border border-white/20 px-4 py-1">
              Updated {new Date(strategy.updated_at).toLocaleDateString()}
            </span>
            {!hasBacktestResults && (
              <span className="rounded-full border border-yellow-500/40 bg-yellow-500/10 px-4 py-1 text-yellow-400">
                Backtest Pending
              </span>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <ModalCard title="Strategy code" subtitle="Inspect generated script" onClick={() => setActiveModal("code")}>
          {codeContent ? (
            <pre className="max-h-24 overflow-hidden text-xs text-white/70 font-mono leading-relaxed">
              {codePreview}
            </pre>
          ) : (
            <div className="flex items-center gap-2 text-xs text-white/50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span>Code will be available after backtest</span>
            </div>
          )}
        </ModalCard>
        <ModalCard title="Performance graph" subtitle="Equity curve snapshot" onClick={() => setActiveModal("chart")}>
          {plotHtml ? (
            <div className="h-32 overflow-hidden rounded bg-white">
              <iframe
                srcDoc={plotHtml}
                className="w-full h-full border-0 pointer-events-none"
                title="Performance Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            </div>
          ) : (
            <div className="h-32 flex flex-col items-center justify-center gap-2 text-white/50 text-sm">
              <div className="animate-pulse">
                <svg className="w-12 h-12 text-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <span>Waiting for backtest...</span>
            </div>
          )}
        </ModalCard>
        <ModalCard title="Performance matrix" subtitle="Tap for full table" onClick={() => setActiveModal("metrics")}>
          <ul className="space-y-2 text-sm text-white/80">
            {quickStats.map((stat) => (
              <li key={stat.label} className="flex items-center justify-between">
                <span className="text-white/50">{stat.label}</span>
                <span className="font-semibold">{stat.value || "--"}</span>
              </li>
            ))}
          </ul>
        </ModalCard>
      </div>

     <InsightModal open={activeModal === "code"} onClose={() => setActiveModal(null)} title="Strategy code">
        {codeContent ? (
          <>
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs text-white/50">Generated Python backtest script</p>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(codeContent)
                }}
                className="text-xs text-secondary hover:text-secondary/80 underline"
              >
                Copy to clipboard
              </button>
            </div>
            <pre className="max-h-[65vh] overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-relaxed text-white/80 font-mono">
              {codeContent}
            </pre>
          </>
        ) : (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/5 mb-4">
              <svg className="w-8 h-8 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <p className="text-sm text-white/70 mb-2">Strategy code not available yet</p>
            <p className="text-xs text-white/50">
              The code will be generated after the first backtest completes
            </p>
          </div>
        )}
      </InsightModal>

      <InsightModal open={activeModal === "chart"} onClose={() => setActiveModal(null)} title="Performance graph">
        {plotHtml ? (
          <>
            <div className="w-full bg-white rounded-2xl overflow-hidden" style={{ height: '600px' }}>
              <iframe
                srcDoc={plotHtml}
                className="w-full h-full border-0"
                title="Performance Chart"
                sandbox="allow-scripts allow-same-origin"
              />
            </div>
            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-white/50">Interactive Bokeh chart from MongoDB</p>
              {dataCsv && (
                <button
                  onClick={() => {
                    const blob = new Blob([dataCsv], { type: 'text/csv' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = 'backtest_data.csv'
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="text-sm text-secondary hover:text-secondary/80 underline"
                >
                  Download data CSV →
                </button>
              )}
            </div>
          </>
        ) : (
          <div className="h-80 flex flex-col items-center justify-center text-white/50">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/5 mb-4 animate-pulse">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-sm mb-2">Performance chart pending</p>
            <p className="text-xs text-white/40">The backtest will generate interactive charts when complete</p>
          </div>
        )}
      </InsightModal>

      <InsightModal open={activeModal === "metrics"} onClose={() => setActiveModal(null)} title="Performance matrix">
        <MetricsTable metrics={metrics} />
      </InsightModal>
    </div>
  )
}

function MetricsTable({ metrics }: { metrics: Record<string, number | string> }) {
  const entries = Object.entries(metrics ?? {})
  if (!entries.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-white/50">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/5 mb-4 animate-pulse">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <p className="text-sm mb-2">Performance metrics pending</p>
        <p className="text-xs text-white/40">Metrics will appear once the backtest completes</p>
      </div>
    )
  }

  // Priority ordering for important metrics
  const priorityOrder = [
    "Return [%]",
    "Sharpe Ratio",
    "Win Rate [%]",
    "# Trades",
    "Max. Drawdown [%]",
    "Buy & Hold Return [%]",
    "CAGR [%]",
    "Sortino Ratio",
    "Calmar Ratio",
  ]

  const sortedEntries = entries.sort((a, b) => {
    const aIndex = priorityOrder.indexOf(a[0])
    const bIndex = priorityOrder.indexOf(b[0])
    if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex
    if (aIndex !== -1) return -1
    if (bIndex !== -1) return 1
    return a[0].localeCompare(b[0])
  })

  const formatValue = (key: string, value: number | string) => {
    if (/\[%\]|return|rate|drawdown/i.test(key)) {
      return formatPercent(value)
    } else if (typeof value === "number") {
      return value.toFixed(2)
    }
    return String(value)
  }

  return (
    <div className="max-h-[65vh] overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-[#050608] border-b border-white/20">
          <tr>
            <th className="py-3 pr-4 text-left text-white/60 font-semibold">Metric</th>
            <th className="py-3 text-right text-white/60 font-semibold">Value</th>
          </tr>
        </thead>
        <tbody>
          {sortedEntries.map(([key, value]) => (
            <tr key={key} className="border-b border-white/10 last:border-none hover:bg-white/5">
              <td className="py-3 pr-4 text-white/70">{key}</td>
              <td className="py-3 text-right font-semibold text-white">{formatValue(key, value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

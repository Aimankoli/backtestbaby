"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { apiClient } from "@/lib/api-client"

type StrategyResponse = {
  id: string
  name: string
  description?: string | null
  status: string
  conversation_id: string
  backtest_results: Array<{
    backtest_id?: string
    metrics?: Record<string, number | string>
    plot_path?: string | null
    ran_at?: string
  }>
  created_at: string
  updated_at: string
}

const parseMetric = (value?: number | string) => {
  if (typeof value === "number") return value
  if (typeof value === "string") {
    const normalized = Number(value.replace(/%/g, ""))
    return Number.isFinite(normalized) ? normalized : undefined
  }
  return undefined
}

const formatPercent = (value?: number | string) => {
  const parsed = parseMetric(value)
  return typeof parsed === "number" ? `${parsed.toFixed(2)}%` : "--"
}

const formatRatio = (value?: number | string) => {
  const parsed = parseMetric(value)
  return typeof parsed === "number" ? parsed.toFixed(2) : "--"
}

const getLatestMetrics = (strategy: StrategyResponse) => {
  if (!strategy.backtest_results?.length) return undefined
  return strategy.backtest_results[strategy.backtest_results.length - 1]?.metrics ?? {}
}

export default function StrategiesTable() {
  const router = useRouter()
  const [strategies, setStrategies] = useState<StrategyResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const data = await apiClient.get<StrategyResponse[]>("/strategies")
        setStrategies(data)
      } catch (err) {
        console.error("Failed to load strategies:", err)
        setError("Unable to load strategies right now.")
      } finally {
        setIsLoading(false)
      }
    }
    fetchStrategies()
  }, [])

  const handleRowClick = (strategyId: string) => {
    router.push(`/chat?strategyId=${strategyId}`)
  }

  const handleDeleteClick = useCallback((strategyId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent row click
    setDeleteConfirmId(strategyId)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteConfirmId) return

    try {
      // Find the strategy to get its conversation_id
      const strategy = strategies.find((s) => s.id === deleteConfirmId)

      // Delete the strategy
      await apiClient.delete(`/strategies/${deleteConfirmId}`)

      // Also delete the associated conversation if it exists
      if (strategy?.conversation_id) {
        try {
          await apiClient.delete(`/conversations/${strategy.conversation_id}`)
        } catch (conversationErr) {
          console.error("Failed to delete associated conversation:", conversationErr)
          // Continue even if conversation deletion fails
        }
      }

      setStrategies((prev) => prev.filter((s) => s.id !== deleteConfirmId))
      setDeleteConfirmId(null)
    } catch (err) {
      console.error("Failed to delete strategy:", err)
      setError("Unable to delete strategy. Please try again.")
      setDeleteConfirmId(null)
    }
  }, [deleteConfirmId, strategies])

  const handleCancelDelete = useCallback(() => {
    setDeleteConfirmId(null)
  }, [])

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-white/60">Loading strategies...</div>
  }

  if (error) {
    return <div className="py-12 text-center text-sm text-destructive">{error}</div>
  }

  if (strategies.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="mb-4 text-white/60">You have not saved any strategies yet.</p>
        <button
          onClick={() => router.push("/chat")}
          className="text-sm font-semibold text-secondary underline-offset-4 hover:underline"
        >
          Start a new conversation
        </button>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-b border-white/10 hover:bg-transparent">
              <TableHead className="font-semibold text-white/70">Strategy</TableHead>
              <TableHead className="font-semibold text-white/70">Status</TableHead>
              <TableHead className="font-semibold text-white/70">Total Return</TableHead>
              <TableHead className="font-semibold text-white/70">Max Drawdown</TableHead>
              <TableHead className="font-semibold text-white/70">Win Rate</TableHead>
              <TableHead className="font-semibold text-white/70">Sharpe Ratio</TableHead>
              <TableHead className="font-semibold text-white/70">Last Updated</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {strategies.map((strategy) => {
              const metrics = getLatestMetrics(strategy) ?? {}
              return (
                <TableRow
                  key={strategy.id}
                  onClick={() => handleRowClick(strategy.id)}
                  className="group relative cursor-pointer border-b border-white/10 hover:bg-white/5 transition"
                >
                  <TableCell className="font-semibold text-white">
                    <div>{strategy.name}</div>
                    {strategy.description && (
                      <p className="text-xs text-white/50">{strategy.description}</p>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-wide text-white/70">
                      {strategy.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-secondary font-semibold">{formatPercent(metrics?.total_return)}</TableCell>
                  <TableCell className="text-white/90">{formatPercent(metrics?.max_drawdown)}</TableCell>
                  <TableCell className="text-white/90">{formatPercent(metrics?.win_rate)}</TableCell>
                  <TableCell className="text-white/90">{formatRatio(metrics?.sharpe_ratio)}</TableCell>
                  <TableCell className="text-sm text-white/60">
                    {new Date(strategy.updated_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    {/* Delete button with animation */}
                    <button
                      onClick={(e) => handleDeleteClick(strategy.id, e)}
                      className="p-2 rounded-lg bg-destructive/80 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-destructive"
                      title="Delete strategy"
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
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={handleCancelDelete}>
          <div
            className="w-full max-w-md rounded-3xl border border-white/20 bg-[#0a0b0f] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-white">Delete Strategy</h3>
              <p className="mt-2 text-sm text-white/60">
                Are you sure you want to delete this strategy? This action cannot be undone.
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
    </>
  )
}

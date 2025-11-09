"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
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

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-muted-foreground">Loading strategies...</div>
  }

  if (error) {
    return <div className="py-12 text-center text-sm text-destructive">{error}</div>
  }

  if (strategies.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="mb-4 text-muted-foreground">You have not saved any strategies yet.</p>
        <button
          onClick={() => router.push("/chat")}
          className="text-sm font-semibold text-accent underline-offset-4 hover:underline"
        >
          Start a new conversation
        </button>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="font-semibold">Strategy</TableHead>
            <TableHead className="font-semibold">Status</TableHead>
            <TableHead className="font-semibold">Total Return</TableHead>
            <TableHead className="font-semibold">Max Drawdown</TableHead>
            <TableHead className="font-semibold">Win Rate</TableHead>
            <TableHead className="font-semibold">Sharpe Ratio</TableHead>
            <TableHead className="font-semibold">Last Updated</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {strategies.map((strategy) => {
            const metrics = getLatestMetrics(strategy) ?? {}
            return (
              <TableRow
                key={strategy.id}
                onClick={() => handleRowClick(strategy.id)}
                className="cursor-pointer hover:bg-muted/40 transition"
              >
                <TableCell className="font-semibold">
                  <div>{strategy.name}</div>
                  {strategy.description && (
                    <p className="text-xs text-muted-foreground">{strategy.description}</p>
                  )}
                </TableCell>
                <TableCell>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs uppercase tracking-wide text-muted-foreground">
                    {strategy.status}
                  </span>
                </TableCell>
                <TableCell className="text-accent font-semibold">{formatPercent(metrics?.total_return)}</TableCell>
                <TableCell>{formatPercent(metrics?.max_drawdown)}</TableCell>
                <TableCell>{formatPercent(metrics?.win_rate)}</TableCell>
                <TableCell>{formatRatio(metrics?.sharpe_ratio)}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(strategy.updated_at).toLocaleString()}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

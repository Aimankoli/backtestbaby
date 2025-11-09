"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, TrendingUp, TrendingDown } from "lucide-react"

type SignalEvent = {
  id: string
  signal_id: string
  tweet_id: string
  tweet_text: string
  tweet_author: string
  sentiment: string
  confidence: number
  ticker_mentioned?: string | null
  action_taken: string[]
  backtest_results?: {
    ticker: string
    strategy: string
    date_range: string
    metrics: {
      total_return?: number
      buy_hold_return?: number
      max_drawdown?: number
      sharpe_ratio?: number
      num_trades?: number
      win_rate?: number
    }
    plot_html?: string
    data_csv?: string
    plot_path?: string
    script_path?: string
  }
  timestamp: string
}

interface SignalEventDetailProps {
  signalId: string
}

export default function SignalEventDetail({ signalId }: SignalEventDetailProps) {
  const [events, setEvents] = useState<SignalEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<SignalEvent | null>(null)

  useEffect(() => {
    fetchEvents()
  }, [signalId])

  const fetchEvents = async () => {
    try {
      const data = await apiClient.get<SignalEvent[]>(`/signals/${signalId}/events`)
      setEvents(data)
      if (data.length > 0) {
        setSelectedEvent(data[0]) // Auto-select latest event
      }
    } catch (err) {
      console.error("Failed to load signal events:", err)
      setError("Unable to load signal events.")
    } finally {
      setIsLoading(false)
    }
  }

  const downloadCSV = (csv: string, ticker: string) => {
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ticker}_backtest_data.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const formatPercent = (value?: number) => {
    if (typeof value !== 'number') return '--'
    return `${value.toFixed(2)}%`
  }

  const formatNumber = (value?: number) => {
    if (typeof value !== 'number') return '--'
    return value.toFixed(2)
  }

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-muted-foreground">Loading events...</div>
  }

  if (error) {
    return <div className="py-12 text-center text-sm text-destructive">{error}</div>
  }

  if (events.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">No signals detected yet. Waiting for tweets...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Event List */}
      <div>
        <h2 className="text-xl font-bold mb-4 text-white">Signal Events ({events.length})</h2>
        <div className="grid gap-3">
          {events.map((event) => (
            <Card
              key={event.id}
              className={`p-4 cursor-pointer transition border-white/10 bg-white/5 hover:border-white/30 ${
                selectedEvent?.id === event.id ? 'border-green-500/40 bg-green-500/10' : ''
              }`}
              onClick={() => setSelectedEvent(event)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {event.sentiment === 'bullish' ? (
                      <TrendingUp className="w-4 h-4 text-green-500" />
                    ) : event.sentiment === 'bearish' ? (
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    ) : (
                      <span className="w-4 h-4" />
                    )}
                    <span className={`font-semibold ${
                      event.sentiment === 'bullish' ? 'text-green-500' :
                      event.sentiment === 'bearish' ? 'text-red-500' :
                      'text-gray-500'
                    }`}>
                      {event.sentiment.toUpperCase()}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      ({(event.confidence * 100).toFixed(0)}% confidence)
                    </span>
                    {event.ticker_mentioned && (
                      <span className="font-mono font-semibold text-accent">${event.ticker_mentioned}</span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">"{event.tweet_text}"</p>
                  <div className="flex gap-2 text-xs text-muted-foreground">
                    <span>{new Date(event.timestamp).toLocaleString()}</span>
                    {event.action_taken.includes('backtest_triggered') && (
                      <span className="text-green-500">• Backtest Run</span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Selected Event Detail */}
      {selectedEvent && selectedEvent.backtest_results && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-2 text-white">Backtest Results</h2>
            <p className="text-sm text-white/60">
              {selectedEvent.backtest_results.ticker} • {selectedEvent.backtest_results.date_range}
            </p>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1">Total Return</div>
              <div className="text-2xl font-bold text-green-400">
                {formatPercent(selectedEvent.backtest_results.metrics.total_return)}
              </div>
            </Card>
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1">Buy & Hold</div>
              <div className="text-2xl font-bold text-white">
                {formatPercent(selectedEvent.backtest_results.metrics.buy_hold_return)}
              </div>
            </Card>
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1">Max Drawdown</div>
              <div className="text-2xl font-bold text-red-400">
                {formatPercent(selectedEvent.backtest_results.metrics.max_drawdown)}
              </div>
            </Card>
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1">Sharpe Ratio</div>
              <div className="text-2xl font-bold text-white">
                {formatNumber(selectedEvent.backtest_results.metrics.sharpe_ratio)}
              </div>
            </Card>
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1"># Trades</div>
              <div className="text-2xl font-bold text-white">
                {selectedEvent.backtest_results.metrics.num_trades ?? '--'}
              </div>
            </Card>
            <Card className="p-4 border-white/10 bg-white/5">
              <div className="text-sm text-white/60 mb-1">Win Rate</div>
              <div className="text-2xl font-bold text-green-400">
                {formatPercent(selectedEvent.backtest_results.metrics.win_rate)}
              </div>
            </Card>
          </div>

          {/* Interactive Chart */}
          {selectedEvent.backtest_results.plot_html && (
            <Card className="p-6 border-white/10 bg-white/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Performance Chart</h3>
              </div>
              <div className="bg-white rounded-lg overflow-hidden">
                <iframe
                  srcDoc={selectedEvent.backtest_results.plot_html}
                  className="w-full h-[600px] border-0"
                  title="Backtest Performance Chart"
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            </Card>
          )}

          {/* Download Data */}
          {selectedEvent.backtest_results.data_csv && (
            <Card className="p-6 border-white/10 bg-white/5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-1 text-white">Historical Data</h3>
                  <p className="text-sm text-white/60">
                    Download the CSV data used for this backtest
                  </p>
                </div>
                <Button
                  onClick={() => downloadCSV(
                    selectedEvent.backtest_results!.data_csv!,
                    selectedEvent.backtest_results!.ticker
                  )}
                  className="gap-2 bg-green-500 hover:bg-green-600 text-white"
                >
                  <Download className="w-4 h-4" />
                  Download CSV
                </Button>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

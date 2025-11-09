"use client"

import { useEffect, useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { apiClient } from "@/lib/api-client"
import SignalEventDetail from "./signal-event-detail"

type SignalResponse = {
  id: string
  twitter_username: string
  ticker?: string | null
  status: string
  last_checked_at?: string | null
  created_at: string
  updated_at: string
  description?: string | null
}

export default function SignalsTable() {
  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null)

  useEffect(() => {
    fetchSignals()
  }, [])

  const fetchSignals = async () => {
    try {
      const data = await apiClient.get<SignalResponse[]>("/signals")
      setSignals(data)
    } catch (err) {
      console.error("Failed to load signals:", err)
      setError("Unable to load signals right now.")
    } finally {
      setIsLoading(false)
    }
  }

  const handlePause = async (e: React.MouseEvent, signalId: string) => {
    e.stopPropagation()
    try {
      await apiClient.post(`/signals/${signalId}/pause`, {})
      fetchSignals()
    } catch (err) {
      console.error("Failed to pause signal:", err)
    }
  }

  const handleResume = async (e: React.MouseEvent, signalId: string) => {
    e.stopPropagation()
    try {
      await apiClient.post(`/signals/${signalId}/resume`, {})
      fetchSignals()
    } catch (err) {
      console.error("Failed to resume signal:", err)
    }
  }

  const handleStop = async (e: React.MouseEvent, signalId: string) => {
    e.stopPropagation()
    if (!confirm("Are you sure you want to stop this signal? This cannot be undone.")) return
    try {
      await apiClient.post(`/signals/${signalId}/stop`, {})
      fetchSignals()
    } catch (err) {
      console.error("Failed to stop signal:", err)
    }
  }

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-muted-foreground">Loading signals...</div>
  }

  if (error) {
    return <div className="py-12 text-center text-sm text-destructive">{error}</div>
  }

  if (signals.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="mb-4 text-muted-foreground">You have not created any signals yet.</p>
        <p className="text-sm text-muted-foreground">
          Create a signal by chatting: <span className="font-mono bg-muted px-2 py-1 rounded">"Monitor @elonmusk for TSLA signals"</span>
        </p>
      </div>
    )
  }

  if (selectedSignalId) {
    return (
      <div>
        <Button
          onClick={() => setSelectedSignalId(null)}
          variant="outline"
          className="mb-4"
        >
          ← Back to Signals
        </Button>
        <SignalEventDetail signalId={selectedSignalId} />
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="font-semibold">Twitter Account</TableHead>
            <TableHead className="font-semibold">Ticker</TableHead>
            <TableHead className="font-semibold">Status</TableHead>
            <TableHead className="font-semibold">Last Checked</TableHead>
            <TableHead className="font-semibold">Created</TableHead>
            <TableHead className="font-semibold">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {signals.map((signal) => (
            <TableRow
              key={signal.id}
              onClick={() => setSelectedSignalId(signal.id)}
              className="cursor-pointer hover:bg-muted/40 transition"
            >
              <TableCell className="font-semibold">
                <div>@{signal.twitter_username}</div>
                {signal.description && (
                  <p className="text-xs text-muted-foreground">{signal.description}</p>
                )}
              </TableCell>
              <TableCell>
                {signal.ticker ? (
                  <span className="font-mono text-sm font-semibold text-accent">${signal.ticker}</span>
                ) : (
                  <span className="text-muted-foreground text-sm">—</span>
                )}
              </TableCell>
              <TableCell>
                <span className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${
                  signal.status === 'active'
                    ? 'bg-green-500/10 text-green-500'
                    : signal.status === 'paused'
                    ? 'bg-yellow-500/10 text-yellow-500'
                    : 'bg-gray-500/10 text-gray-500'
                }`}>
                  {signal.status}
                </span>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {signal.last_checked_at
                  ? new Date(signal.last_checked_at).toLocaleString()
                  : 'Never'
                }
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {new Date(signal.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell>
                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                  {signal.status === 'active' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => handlePause(e, signal.id)}
                    >
                      Pause
                    </Button>
                  )}
                  {signal.status === 'paused' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => handleResume(e, signal.id)}
                    >
                      Resume
                    </Button>
                  )}
                  {signal.status !== 'stopped' && (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={(e) => handleStop(e, signal.id)}
                    >
                      Stop
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

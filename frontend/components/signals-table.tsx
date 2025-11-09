"use client"

import { useEffect, useState, useCallback } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { apiClient } from "@/lib/api-client"
import SignalEventDetail from "./signal-event-detail"
import { style } from "framer-motion/client"

type SignalResponse = {
  id: string
  twitter_username: string
  ticker?: string | null
  status: string
  conversation_id?: string
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
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

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

  const handleDeleteClick = useCallback((signalId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setDeleteConfirmId(signalId)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteConfirmId) return

    try {
      // Find the signal to get its conversation_id
      const signal = signals.find((s) => s.id === deleteConfirmId)

      // Delete the signal
      await apiClient.delete(`/signals/${deleteConfirmId}`)

      // Also delete the associated conversation if it exists
      if (signal?.conversation_id) {
        try {
          await apiClient.delete(`/conversations/${signal.conversation_id}`)
        } catch (conversationErr) {
          console.error("Failed to delete associated conversation:", conversationErr)
          // Continue even if conversation deletion fails
        }
      }

      setSignals((prev) => prev.filter((s) => s.id !== deleteConfirmId))
      setDeleteConfirmId(null)
    } catch (err) {
      console.error("Failed to delete signal:", err)
      setError("Unable to delete signal. Please try again.")
      setDeleteConfirmId(null)
    }
  }, [deleteConfirmId, signals])

  const handleCancelDelete = useCallback(() => {
    setDeleteConfirmId(null)
  }, [])

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-white/60">Loading signals...</div>
  }

  if (error) {
    return <div className="py-12 text-center text-sm text-destructive">{error}</div>
  }

  if (signals.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="mb-4 text-white/60">You have not created any signals yet.</p>
        <p className="text-sm text-white/50">
          Create a signal by chatting: <span className="font-mono bg-white/10 px-2 py-1 rounded">"Monitor @elonmusk for TSLA signals"</span>
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
          className="mb-4 rounded-xl border-white/20 text-white hover:bg-white/10"
        >
          ← Back to Signals
        </Button>
        <SignalEventDetail signalId={selectedSignalId} />
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-b border-white/10 hover:bg-transparent">
              <TableHead className="font-semibold text-white/70">Twitter Account</TableHead>
              <TableHead className="font-semibold text-white/70">Ticker</TableHead>
              <TableHead className="font-semibold text-white/70">Status</TableHead>
              <TableHead className="font-semibold text-white/70">Last Checked</TableHead>
              <TableHead className="font-semibold text-white/70">Created</TableHead>
              <TableHead className="font-semibold text-white/70">Actions</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {signals.map((signal) => (
              <TableRow
                key={signal.id}
                onClick={() => setSelectedSignalId(signal.id)}
                className="group cursor-pointer border-b border-white/10 hover:bg-white/5 transition"
              >
                <TableCell className="font-semibold text-white">
                  <div>@{signal.twitter_username}</div>
                  {signal.description && (
                    <p className="text-xs text-white/50">{signal.description}</p>
                  )}
                </TableCell>
                <TableCell>
                  {signal.ticker ? (
                    <span className="font-mono text-sm font-semibold text-secondary">${signal.ticker}</span>
                  ) : (
                    <span className="text-white/50 text-sm">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <span className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${
                    signal.status === 'active'
                      ? 'bg-green-500/20 text-green-400'
                      : signal.status === 'paused'
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-gray-500/20 text-gray-400'
                  }`}>
                    {signal.status}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-white/60">
                  {signal.last_checked_at
                    ? new Date(signal.last_checked_at).toLocaleString()
                    : 'Never'
                  }
                </TableCell>
                <TableCell className="text-sm text-white/60">
                  {new Date(signal.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    {signal.status === 'active' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-lg border-white/20 text-white hover:bg-white/10"
                        onClick={(e) => handlePause(e, signal.id)}
                        style={{ color: "black" }}
                      >
                        Pause
                      </Button>
                    )}
                    {signal.status === 'paused' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-lg border-white/20 text-white hover:bg-white/10"
                        onClick={(e) => handleResume(e, signal.id)}
                        style={{ color: "black" }}
                      >
                        Resume
                      </Button>
                    )}
                    {signal.status !== 'stopped' && (
                      <Button
                        size="sm"
                        variant="destructive"
                        className="rounded-lg"
                        onClick={(e) => handleStop(e, signal.id)}
                      >
                        Stop
                      </Button>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  {/* Delete button with animation */}
                  <button
                    onClick={(e) => handleDeleteClick(signal.id, e)}
                    className="p-2 rounded-lg bg-destructive/80 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-destructive"
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
                </TableCell>
              </TableRow>
            ))}
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
              <h3 className="text-xl font-semibold text-white">Delete Signal</h3>
              <p className="mt-2 text-sm text-white/60">
                Are you sure you want to delete this signal? This action cannot be undone.
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

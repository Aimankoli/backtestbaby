"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import SignalsTable from "@/components/signals-table"
import { apiClient } from "@/lib/api-client"

interface UserResponse {
  id: string
  username: string
  email: string
}

export default function SignalsPage() {
  const router = useRouter()
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await apiClient.get<UserResponse>("/auth/me")
        setUser(userData)
      } catch {
        router.push("/login")
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [router])

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout")
      router.push("/")
    } catch (err) {
      console.error("Logout failed:", err)
    }
  }

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return (
    <main className="min-h-screen bg-[#050608] text-white">
      {/* Navigation */}
      <nav className="border-b border-white/10 bg-[#0a0b0f] px-8 py-5 flex items-center justify-between">
        <Link href="/chat" className="text-2xl font-bold hover:text-secondary transition">
          ⚡ Backtest Sandbox
        </Link>
        <div className="flex items-center gap-6">
          <Link href="/chat" className="text-sm text-white/70 hover:text-secondary transition">
            New Chat
          </Link>
          <Link href="/research" className="text-sm text-white/70 hover:text-secondary transition">
            Research
          </Link>
          <Link href="/strategies" className="text-sm text-white/70 hover:text-secondary transition">
            Strategies
          </Link>
          <Link href="/signals" className="text-sm text-secondary">
            Signals
          </Link>
          <div className="text-sm text-white/60">{user?.username}</div>
          <Button
            variant="outline"
            className="rounded-xl border-white/20 text-white hover:bg-white/10 bg-transparent"
            onClick={handleLogout}
          >
            Logout
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-8">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.4em] text-white/40 mb-2">Signal Monitor</p>
          <h1 className="text-4xl font-bold mb-2">My Signals</h1>
          <p className="text-white/60">Twitter sentiment signals and their backtest results</p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <SignalsTable />
        </div>
      </div>
    </main>
  )
}

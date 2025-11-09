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
    <main className="min-h-screen bg-background">
      <div className="h-1 bg-secondary w-full" />

      {/* Navigation */}
      <nav className="bg-primary text-primary-foreground px-6 py-4 flex items-center justify-between">
        <Link href="/chat" className="text-2xl font-bold">
          ⚡ Backtest Sandbox
        </Link>
        <div className="flex items-center gap-6">
          <Link href="/chat" className="hover:text-secondary transition">
            New Chat
          </Link>
          <Link href="/strategies" className="hover:text-secondary transition">
            Strategies
          </Link>
          <Link href="/signals" className="text-secondary">
            Signals
          </Link>
          <div className="text-sm">{user?.username}</div>
          <Button
            variant="outline"
            className="border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary bg-transparent"
            onClick={handleLogout}
          >
            Logout
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Signals</h1>
          <p className="text-muted-foreground">Twitter sentiment signals and their backtest results</p>
        </div>

        <Card className="p-6">
          <SignalsTable />
        </Card>
      </div>
    </main>
  )
}

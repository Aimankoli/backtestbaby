"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import ResearchChat from "@/components/research-chat"
import { apiClient } from "@/lib/api-client"

interface UserResponse {
  id: string
  username: string
  email: string
}

function ResearchContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const initialConversationId = searchParams.get("conversationId")

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
    <main className="min-h-screen bg-[#050608]">
      <div className="h-1 bg-secondary w-full" />

      {/* Navigation */}
      <nav className="bg-primary text-primary-foreground px-6 py-4 flex items-center justify-between">
        <Link href="/dashboard" className="text-2xl font-bold">
          ⚡ Backtest Baby
        </Link>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="hover:text-secondary transition">
            Dashboard
          </Link>
          <Link href="/chat" className="hover:text-secondary transition">
            Strategy Chat
          </Link>
          <Link href="/strategies" className="hover:text-secondary transition">
            Strategies
          </Link>
          <Link href="/signals" className="hover:text-secondary transition">
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
      <ResearchChat initialConversationId={initialConversationId} />
    </main>
  )
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen bg-[#050608] text-white">Loading...</div>}>
      <ResearchContent />
    </Suspense>
  )
}

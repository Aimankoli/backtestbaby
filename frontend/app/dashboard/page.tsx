"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { apiClient } from "@/lib/api-client"
import { motion } from "framer-motion"

interface UserResponse {
  id: string
  username: string
  email: string
}

export default function DashboardPage() {
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
    return <div className="flex items-center justify-center min-h-screen bg-[#050608] text-white">Loading...</div>
  }

  const navigationCards = [
    {
      title: "Strategy Chat",
      description: "Create and backtest trading strategies with AI assistance",
      href: "/chat",
      color: "from-blue-500/10 to-blue-600/5",
      borderColor: "hover:border-blue-500/30",
    },
    {
      title: "Research",
      description: "Explore market data and conduct in-depth research analysis",
      href: "/research",
      color: "from-purple-500/10 to-purple-600/5",
      borderColor: "hover:border-purple-500/30",
    },
    {
      title: "Strategies",
      description: "View and manage all your saved backtested strategies",
      href: "/strategies",
      color: "from-green-500/10 to-green-600/5",
      borderColor: "hover:border-green-500/30",
    },
  ]

  return (
    <main className="min-h-screen bg-[#050608] text-white relative overflow-hidden">
      {/* Yellowish light background effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-secondary/5 via-transparent to-transparent pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-secondary/10 blur-[120px] rounded-full pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-20 border-b border-white/10 bg-[#0a0b0f]/80 backdrop-blur-sm px-8 py-5 flex items-center justify-between">
        <Link href="/dashboard" className="text-2xl font-bold hover:text-secondary transition">
          ⚡ Backtest Baby
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
          <Link href="/signals" className="text-sm text-white/70 hover:text-secondary transition">
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
      <div className="relative z-10 max-w-6xl mx-auto px-8 py-16">
        <motion.div
          className="mb-12 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-xs uppercase tracking-[0.4em] text-white/40 mb-3">Dashboard</p>
          <h1 className="text-5xl font-bold mb-4">
            Welcome back, <span className="text-secondary">{user?.username}</span>
          </h1>
          <p className="text-white/60 text-lg">Choose where you'd like to go</p>
        </motion.div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {navigationCards.map((card, idx) => (
            <motion.div
              key={card.href}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 + idx * 0.1 }}
            >
              <Link href={card.href}>
                <div
                  className={`group relative p-8 rounded-3xl border border-white/10 bg-gradient-to-br ${card.color} hover:bg-white/10 ${card.borderColor} transition-all cursor-pointer h-full`}
                >
                  <h3 className="text-2xl font-semibold mb-3 text-white group-hover:text-secondary transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-white/60 leading-relaxed mb-6">{card.description}</p>
                  <div className="flex items-center text-secondary text-sm font-semibold group-hover:translate-x-2 transition-transform">
                    Open <span className="ml-2">→</span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Quick Stats Section */}
        <motion.div
          className="rounded-3xl border border-white/10 bg-white/5 p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          <h2 className="text-2xl font-bold mb-6 text-white">Getting Started</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <h4 className="text-sm uppercase tracking-wide text-white/40 mb-2">Step 1</h4>
              <h3 className="text-lg font-semibold text-white mb-2">Create a Strategy</h3>
              <p className="text-sm text-white/60">
                Go to Strategy Chat and describe your trading strategy in plain English
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <h4 className="text-sm uppercase tracking-wide text-white/40 mb-2">Step 2</h4>
              <h3 className="text-lg font-semibold text-white mb-2">Review Results</h3>
              <p className="text-sm text-white/60">
                Analyze backtest results with comprehensive metrics and visualizations
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <h4 className="text-sm uppercase tracking-wide text-white/40 mb-2">Step 3</h4>
              <h3 className="text-lg font-semibold text-white mb-2">Monitor Signals</h3>
              <p className="text-sm text-white/60">
                Set up Twitter signal monitoring for real-time sentiment analysis
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  )
}

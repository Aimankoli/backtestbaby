"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { motion } from "framer-motion"

export default function Home() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check if user is authenticated
    const checkAuth = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/me`, {
          credentials: "include",
        })
        if (response.ok) {
          setIsAuthenticated(true)
          router.push("/dashboard")
        }
      } catch {
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [router])

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return (
    <main className="relative min-h-screen bg-[#050608] overflow-hidden text-white">
      {/* Yellowish light background effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-secondary/5 via-transparent to-transparent pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-secondary/10 blur-[120px] rounded-full pointer-events-none" />

      <nav className="relative z-20 border-b border-white/10 bg-[#0a0b0f]/80 backdrop-blur-sm px-8 py-5 flex items-center justify-between">
        <motion.div
          className="text-2xl font-bold"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          ⚡ Backtest Baby
        </motion.div>
        <motion.div
          className="flex gap-4"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Link href="/login">
            <Button
              variant="outline"
              className="rounded-xl border-white/20 text-white hover:bg-white/10 bg-transparent"
            >
              Login
            </Button>
          </Link>
          <Link href="/signup">
            <Button className="rounded-xl bg-secondary text-black hover:bg-secondary/90">Sign Up</Button>
          </Link>
        </motion.div>
      </nav>

      <section className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 py-12">
        <div className="max-w-6xl mx-auto w-full">
          {/* Main heading */}
          <motion.h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6 text-balance text-white text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Test Trading <span className="text-secondary">Strategies</span> with Historical Data
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="text-base sm:text-lg text-white/60 mb-12 text-center max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Write natural language strategy prompts and backtest them instantly with real Yahoo Finance data. Powered by
            AI and historical market insights.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            className="flex justify-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Link href="/signup">
              <Button
                size="lg"
                className="rounded-full bg-secondary text-black hover:bg-secondary/90 px-10 py-6 text-lg font-semibold"
              >
                Get Started Free
              </Button>
            </Link>
          </motion.div>

          {/* Feature Cards */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            {[
              {
                title: "Natural Language",
                desc: "Describe your strategy in plain English. No coding required - just tell us what you want to test.",
              },
              {
                title: "Real Market Data",
                desc: "Backtest with historical data from Yahoo Finance. Get accurate results based on real market conditions.",
              },
              {
                title: "Instant Results",
                desc: "Get comprehensive performance metrics, visualizations, and insights in seconds.",
              },
              {
                title: "AI-Powered",
                desc: "Our AI understands complex trading strategies and converts them into executable backtests.",
              },
              {
                title: "Twitter Signals",
                desc: "Monitor Twitter accounts for trading signals and automatically backtest sentiment-based strategies.",
              },
              {
                title: "Strategy Library",
                desc: "Save and manage all your strategies in one place. Compare performance across different approaches.",
              },
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                className="p-6 rounded-3xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-secondary/30 transition-all group"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.7 + idx * 0.1 }}
              >
                <h3 className="font-semibold text-xl mb-3 text-white group-hover:text-secondary transition-colors">{feature.title}</h3>
                <p className="text-sm text-white/60 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    </main>
  )
}

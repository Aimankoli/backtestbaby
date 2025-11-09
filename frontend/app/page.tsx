"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { motion } from "framer-motion"
import Image from "next/image"

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
          router.push("/chat")
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
    <main className="relative min-h-screen bg-background overflow-hidden">
      <div className="h-1 bg-secondary w-full relative z-20" />

      <nav className="relative z-20 bg-primary text-primary-foreground px-6 py-4 flex items-center justify-between">
        <motion.div
          className="text-xl font-bold"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          ⚡ Backtest Sandbox
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
              className="border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary bg-transparent"
            >
              Login
            </Button>
          </Link>
          <Link href="/signup">
            <Button className="bg-secondary text-secondary-foreground hover:bg-accent">Sign Up</Button>
          </Link>
        </motion.div>
      </nav>

      <section className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 py-12">
        <div className="max-w-4xl mx-auto w-full">
          {/* Main heading */}
          <motion.h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6 text-balance text-foreground text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Test Trading <span className="text-secondary">Strategies</span> with Historical Data
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="text-base sm:text-lg text-muted-foreground mb-8 text-center max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Write natural language strategy prompts and backtest them instantly with real Yahoo Finance data. Powered by
            AI and historical market insights.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            className="flex justify-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Link href="/signup">
              <Button
                size="lg"
                className="bg-secondary text-secondary-foreground hover:bg-accent px-8 py-6 text-base font-semibold"
              >
                Get Started Free
              </Button>
            </Link>
          </motion.div>

          {/* Dashboard Image */}
          <motion.div
            className="w-full max-w-4xl mx-auto mb-12"
            initial={{ opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 1, delay: 0.6 }}
          >
            <div className="relative w-full aspect-video rounded-lg sm:rounded-xl overflow-hidden shadow-2xl border border-border">
              <Image
                src="/images/dash.png"
                alt="Backtest Dashboard Interface"
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 768px) 90vw, (max-width: 1024px) 80vw, 1200px"
                className="object-cover"
                priority
              />
            </div>
          </motion.div>

          {/* Feature highlights */}
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-3 gap-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
          >
            {[
              { title: "Natural Language", desc: "Describe your strategy in plain English" },
              { title: "Real Data", desc: "Backtest with Yahoo Finance historical data" },
              { title: "Instant Results", desc: "Get performance metrics and visualizations" },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="p-6 rounded-lg bg-card/50 backdrop-blur border border-border/50 hover:border-secondary/50 transition-all"
              >
                <h3 className="font-semibold text-base mb-2 text-secondary">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>
    </main>
  )
}

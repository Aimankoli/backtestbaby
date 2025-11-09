"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { apiClient } from "@/lib/api-client"

export default function Login() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      await apiClient.post("/auth/login", formData)
      router.push("/chat")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#050608] flex items-center justify-center text-white relative overflow-hidden">
      {/* Yellowish glow effect behind login box */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-secondary/15 blur-[150px] rounded-full pointer-events-none" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 border-b border-white/10 bg-[#0a0b0f]/80 backdrop-blur-sm px-8 py-5 flex items-center justify-between z-50">
        <Link href="/" className="text-2xl font-bold hover:text-secondary transition">
          ⚡ Backtest Baby
        </Link>
        <div className="flex gap-4">
          <Link href="/signup">
            <Button className="rounded-xl bg-secondary text-black hover:bg-secondary/90">Sign Up</Button>
          </Link>
        </div>
      </nav>

      <div className="w-full max-w-md p-8 mt-16 rounded-3xl border border-white/10 bg-white/5 relative z-10">
        <h1 className="text-3xl font-bold mb-2 text-white">Welcome Back</h1>
        <p className="text-white/60 mb-6">Login to your account</p>

        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-white">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-white/20 rounded-xl bg-white/5 text-white focus:ring-2 focus:ring-secondary focus:border-transparent outline-none placeholder:text-white/40"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-white">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-white/20 rounded-xl bg-white/5 text-white focus:ring-2 focus:ring-secondary focus:border-transparent outline-none placeholder:text-white/40"
              placeholder="••••••"
            />
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-secondary text-black hover:bg-secondary/90 h-12 mt-6 font-semibold"
          >
            {isLoading ? "Logging In..." : "Login"}
          </Button>
        </form>

        <p className="text-center text-sm text-white/60 mt-6">
          Don't have an account?{" "}
          <Link href="/signup" className="text-secondary font-semibold hover:underline">
            Sign Up
          </Link>
        </p>
      </div>
    </main>
  )
}

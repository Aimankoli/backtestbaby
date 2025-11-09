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
    <main className="min-h-screen bg-gradient-to-br from-secondary via-background to-background flex items-center justify-center">
      <div className="h-1 bg-secondary fixed top-0 w-full" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-primary text-primary-foreground px-6 py-4 flex items-center justify-between h-16">
        <Link href="/" className="text-2xl font-bold">
          ⚡
        </Link>
        <div className="flex gap-4">
          <Link href="/signup">
            <Button className="bg-secondary text-secondary-foreground hover:bg-accent">Sign Up</Button>
          </Link>
        </div>
      </nav>

      <Card className="w-full max-w-md p-8 mt-16">
        <h1 className="text-3xl font-bold mb-2">Welcome Back</h1>
        <p className="text-muted-foreground mb-6">Login to your account</p>

        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-accent focus:border-transparent outline-none"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-accent focus:border-transparent outline-none"
              placeholder="••••••"
            />
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-10 mt-6"
          >
            {isLoading ? "Logging In..." : "Login"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Don't have an account?{" "}
          <Link href="/signup" className="text-accent font-semibold hover:underline">
            Sign Up
          </Link>
        </p>
      </Card>
    </main>
  )
}

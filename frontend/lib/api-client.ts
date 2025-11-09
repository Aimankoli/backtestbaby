const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const apiClient = {
  async post<T>(endpoint: string, body?: Record<string, unknown>): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body || {}),
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  },

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  },

  async delete<T>(endpoint: string): Promise<T | null> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      credentials: "include",
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    // Handle 204 No Content - no body to parse
    if (response.status === 204) {
      return null as T | null
    }
    return response.json()
  },
}

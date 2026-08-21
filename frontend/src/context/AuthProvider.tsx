import { useEffect, useState, type ReactNode } from 'react'
import { authApi, getToken, clearTokens } from '../api'
import { AuthContext, type User } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(getToken()))

  useEffect(() => {
    if (!getToken()) return
    let cancelled = false
    authApi.profile()
      .then((profile) => {
        if (!cancelled) setUser(profile)
      })
      .catch(() => clearTokens())
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = async (email: string, password: string) => {
    const tokens = await authApi.login(email, password)
    localStorage.setItem('vouch_access', tokens.access)
    localStorage.setItem('vouch_refresh', tokens.refresh)
    const profile = await authApi.profile()
    setUser(profile)
  }

  const register = async (email: string, password: string) => {
    await authApi.register(email, password)
    await login(email, password)
  }

  const logout = () => {
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

import { createContext, useContext, useEffect, useState } from 'react'
import api from '../services/api'
const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); const [loading, setLoading] = useState(!!localStorage.getItem('token'))
  useEffect(() => { if (localStorage.getItem('token')) api.get('/auth/me').then((r) => setUser(r.data)).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false)) }, [])
  const login = async (email, password) => { const r = await api.post('/auth/login', { email, password }); localStorage.setItem('token', r.data.access_token); setUser(r.data.user) }
  const logout = () => { localStorage.removeItem('token'); setUser(null) }
  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>
}

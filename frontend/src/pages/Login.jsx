import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Alert } from '../components/ui'
import { errMsg } from '../services/api'
export default function Login() {
  const { login } = useAuth(); const nav = useNavigate(); const [f, setF] = useState({ email: '', password: '' }); const [err, setErr] = useState('')
  const submit = async (e) => { e.preventDefault(); try { await login(f.email, f.password); nav('/') } catch (x) { setErr(errMsg(x)) } }
  return <div className="min-h-screen grid place-items-center bg-navy-50 p-4"><form onSubmit={submit} className="card w-full max-w-sm space-y-3">
    <h1 className="text-xl font-semibold text-navy-900">AI Timetable Optimization</h1><p className="text-sm text-slate-500">Sign in to your college account</p><Alert kind="error">{err}</Alert>
    <div><label className="label">Email</label><input className="input" type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
    <div><label className="label">Password</label><input className="input" type="password" required value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></div>
    <button className="btn w-full">Sign in</button></form></div>
}

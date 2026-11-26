import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { useAuth } from '../context/AuthContext'
import { Stat, useLoad, Alert } from '../components/ui'
export default function Dashboard() {
  const { user } = useAuth(); const [d, err] = useLoad('/dashboard'); const [notes] = useLoad('/notifications')
  if (!d) return <Alert kind="error">{err}</Alert>
  const skip = ['published_version_id', 'published_name']
  const stats = Object.entries(d).filter(([k]) => !skip.includes(k))
  return <div><h1 className="h1">{user.role.toUpperCase()} Dashboard</h1><Alert kind="error">{err}</Alert>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">{stats.map(([k, v]) => <Stat key={k} label={k.replaceAll('_', ' ')} value={v} />)}</div>
    <div className="card mb-4">Published timetable: {d.published_version_id ? <Link className="text-navy-700 underline" to="/timetable">#{d.published_version_id} {d.published_name}</Link> : <span className="text-slate-500">none yet</span>}</div>
    {user.role === 'admin' && <div className="card mb-4 h-64"><ResponsiveContainer><BarChart data={stats.filter(([, v]) => typeof v === 'number').map(([k, v]) => ({ name: k.replaceAll('_', ' '), value: v }))}><XAxis dataKey="name" tick={{ fontSize: 10 }} /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" fill="#1e3a8a" /></BarChart></ResponsiveContainer></div>}
    <div className="card"><h2 className="font-semibold mb-2">Notifications</h2>{(notes || []).slice(0, 8).map((n) => <div key={n.id} className="text-sm border-b py-1"><b>{n.title}</b> <span className="text-slate-500">{n.message}</span></div>)}{!(notes || []).length && <span className="text-slate-400 text-sm">Nothing new</span>}</div></div>
}

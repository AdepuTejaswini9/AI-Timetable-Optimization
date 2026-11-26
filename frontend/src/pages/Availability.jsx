import { useEffect, useState } from 'react'
import api, { errMsg } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Alert, DAYS, useLoad } from '../components/ui'
const STATES = ['available', 'unavailable', 'avoid']; const COLORS = { available: 'bg-green-100', unavailable: 'bg-red-200', avoid: 'bg-amber-100' }

export default function Availability() {
  const { user } = useAuth(); const [me] = useLoad('/auth/me'); const [facs] = useLoad(user.role === 'admin' ? '/faculty' : null); const [slots] = useLoad('/config/timeslots')
  const [fid, setFid] = useState(null); const [grid, setGrid] = useState({}); const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  useEffect(() => { if (user.role === 'faculty' && me?.faculty_id) setFid(me.faculty_id) }, [me])
  useEffect(() => { if (!fid) return; api.get(`/faculty/${fid}/availability`).then((r) => { const g = {}; r.data.unavailable.forEach((s) => (g[`${s.day}-${s.period}`] = 'unavailable')); r.data.avoid.forEach((s) => (g[`${s.day}-${s.period}`] = 'avoid')); setGrid(g) }).catch((e) => setErr(errMsg(e))) }, [fid])
  const days = slots ? Math.max(...slots.slots.map((s) => s.day)) + 1 : 5; const periods = slots ? [...new Set(slots.slots.map((s) => s.period))] : []
  const cycle = (k) => setGrid({ ...grid, [k]: STATES[(STATES.indexOf(grid[k] || 'available') + 1) % 3] })
  const save = async () => { const pick = (st) => Object.keys(grid).filter((k) => grid[k] === st).map((k) => { const [day, period] = k.split('-').map(Number); return { day, period } })
    try { await api.put(`/faculty/${fid}/availability`, { unavailable: pick('unavailable'), avoid: pick('avoid'), preferred: [] }); setMsg('Availability saved. It applies the next time a timetable is generated.'); setErr('') } catch (e) { setErr(errMsg(e)) } }
  return <div><h1 className="h1">Faculty Availability & Preferences</h1><p className="text-sm text-slate-500 mb-3">Click a cell to cycle: available → unavailable (hard constraint) → avoid (soft preference).</p>
    {user.role === 'admin' && <select className="input max-w-xs mb-3" value={fid || ''} onChange={(e) => setFid(+e.target.value)}><option value="">Select faculty…</option>{(facs || []).map((f) => <option key={f.id} value={f.id}>{f.full_name}</option>)}</select>}
    <Alert kind="error">{err}</Alert><Alert kind="ok">{msg}</Alert>
    {fid && <div className="card inline-block"><table><thead><tr><th></th>{DAYS.slice(0, days).map((d) => <th key={d} className="px-3 text-sm">{d}</th>)}</tr></thead><tbody>{periods.map((p) => <tr key={p}><td className="pr-3 text-sm">P{p + 1}</td>{Array.from({ length: days }).map((_, d) => { const s = grid[`${d}-${p}`] || 'available'; return <td key={d} className="p-1"><button onClick={() => cycle(`${d}-${p}`)} className={`w-24 h-9 rounded text-xs ${COLORS[s]}`}>{s}</button></td> })}</tr>)}</tbody></table><button className="btn mt-3" onClick={save}>Save</button></div>}</div>
}

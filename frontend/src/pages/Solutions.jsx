import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import api, { errMsg } from '../services/api'
import TimetableGrid from '../components/TimetableGrid'
import { Alert, Table, useLoad } from '../components/ui'
const OBJ = ['student_free_periods', 'faculty_preference_violations', 'excess_consecutive_teaching', 'room_underutilization', 'subject_distribution']

export default function Solutions() {
  const [sp, setSp] = useSearchParams(); const runId = sp.get('run')
  const [runs] = useLoad('/optimization'); const [sols, err, reload] = useLoad(runId ? `/optimization/${runId}/solutions` : null, [runId])
  const [secs] = useLoad('/sections'); const [slots] = useLoad('/config/timeslots')
  const [x, setX] = useState(OBJ[0]); const [y, setY] = useState(OBJ[3]); const [pick, setPick] = useState(null); const [sec, setSec] = useState('')
  const [entries, setEntries] = useState([]); const [msg, setMsg] = useState(''); const [e2, setE2] = useState('')
  useEffect(() => { if (!pick) return; api.get(`/optimization/solutions/${pick.id}/entries${sec ? `?section_id=${sec}` : ''}`).then((r) => setEntries(r.data)).catch((e) => setE2(errMsg(e))) }, [pick, sec])
  const select = async () => { try { const r = await api.post(`/optimization/${runId}/select`, { solution_id: pick.id }); setMsg(`Draft timetable #${r.data.version_id} created. Submit it for approval under "Approvals & Publish".`); reload() } catch (e) { setE2(errMsg(e)) } }
  const grid = slots ? { days: Math.max(...slots.slots.map((s) => s.day)) + 1, periods: slots.slots.filter((s) => s.day === 0).map((s) => ({ period: s.period, start: s.start_time, end: s.end_time })) } : null
  const data = (sols || []).map((s) => ({ ...s.objectives, id: s.id, rank: s.rank + 1 }))
  return <div><h1 className="h1">Compare Solutions & Pareto Front</h1><Alert kind="error">{err || e2}</Alert><Alert kind="ok">{msg}</Alert>
    <div className="card mb-4 flex gap-3 items-end"><div><label className="label">Optimization run</label><select className="input" value={runId || ''} onChange={(e) => setSp({ run: e.target.value })}><option value="">Select…</option>{(runs || []).filter((r) => r.outcome === 'feasible_found').map((r) => <option key={r.id} value={r.id}>#{r.id} {r.algorithm}</option>)}</select></div>
      <div><label className="label">X axis</label><select className="input" value={x} onChange={(e) => setX(e.target.value)}>{OBJ.map((o) => <option key={o}>{o}</option>)}</select></div>
      <div><label className="label">Y axis</label><select className="input" value={y} onChange={(e) => setY(e.target.value)}>{OBJ.map((o) => <option key={o}>{o}</option>)}</select></div></div>
    {data.length > 0 && <div className="grid md:grid-cols-2 gap-4 mb-4">
      <div className="card h-80"><div className="text-sm font-semibold mb-1">Pareto front (all points feasible; lower is better)</div><ResponsiveContainer><ScatterChart margin={{ left: 10, bottom: 20 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" dataKey={x} name={x} label={{ value: x, position: 'bottom', fontSize: 11 }} /><YAxis type="number" dataKey={y} name={y} /><ZAxis range={[80, 80]} /><Tooltip /><Scatter data={data} fill="#1e3a8a" onClick={(d) => setPick(sols.find((s) => s.id === d.id))} /></ScatterChart></ResponsiveContainer></div>
      <div className="card p-0"><Table cols={[{ label: '#', render: (r) => r.rank }, ...OBJ.map((o) => ({ key: o, label: o.split('_').slice(0, 2).join(' ') })), { label: '', render: (r) => <button className="btn-ghost" onClick={() => setPick(sols.find((s) => s.id === r.id))}>Preview</button> }]} rows={data} /></div></div>}
    {pick && <div className="card"><div className="flex items-end gap-3 mb-3"><b>Solution #{pick.rank + 1}</b>{pick.is_selected && <span className="text-green-700 text-sm">selected (version #{pick.version_id})</span>}
      <div><label className="label">Section</label><select className="input" value={sec} onChange={(e) => setSec(e.target.value)}><option value="">All sections</option>{(secs || []).map((s) => <option key={s.id} value={s.id}>{s.name} (dept {s.department_id})</option>)}</select></div>
      <button className="btn" onClick={select}>Select & create draft timetable</button></div>
      {grid && <TimetableGrid entries={entries} grid={grid} />}</div>}</div>
}

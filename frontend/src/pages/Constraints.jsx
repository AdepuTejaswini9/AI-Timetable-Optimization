import { useEffect, useState } from 'react'
import api, { errMsg } from '../services/api'
import { Alert, useLoad } from '../components/ui'
const SOFT = ['student_free_periods', 'faculty_preference_violations', 'excess_consecutive_teaching', 'room_underutilization', 'subject_distribution']
const HARD = ['No faculty double-booking', 'No room double-booking', 'No section double-booking', 'Room capacity ≥ section strength', 'Faculty availability respected', 'Required weekly hours fully scheduled', 'Labs only in laboratory rooms', 'Lab blocks are consecutive periods and never cross the lunch break', 'Faculty daily / weekly hour limits', 'All entries reference valid subject assignments']

export default function Constraints() {
  const [st, , reload] = useLoad('/settings'); const [slots, , rs] = useLoad('/config/timeslots'); const [w, setW] = useState({}); const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [cfg, setCfg] = useState({ days: 5, periods: 6, first_start: '09:00', period_minutes: 50, gap_minutes: 10, break_after_period: 2, lunch_minutes: 60 })
  useEffect(() => { if (st) setW(st) }, [st])
  const save = async () => { try { await api.put('/settings', { values: w }); setMsg('Settings saved'); setErr(''); reload() } catch (e) { setErr(errMsg(e)) } }
  const saveSlots = async () => { try { await api.put('/config/timeslots', Object.fromEntries(Object.entries(cfg).map(([k, v]) => [k, k === 'first_start' ? v : Number(v)]))); setMsg('Period grid updated'); setErr(''); rs() } catch (e) { setErr(errMsg(e)) } }
  return <div><h1 className="h1">Constraints & Period Configuration</h1><Alert kind="error">{err}</Alert><Alert kind="ok">{msg}</Alert>
    <div className="grid md:grid-cols-2 gap-4">
      <div className="card"><h2 className="font-semibold mb-2">Hard constraints (always enforced)</h2><ul className="list-disc ml-5 text-sm space-y-1">{HARD.map((h) => <li key={h}>{h}</li>)}</ul><p className="text-xs text-slate-500 mt-2">Hard constraints cannot be traded against soft objectives or disabled.</p></div>
      <div className="card"><h2 className="font-semibold mb-2">Soft objective weights (used by the GA baseline; NSGA-II keeps objectives separate)</h2>
        {SOFT.map((s) => <div key={s} className="flex items-center gap-2 mb-2"><label className="text-sm w-64">{s.replaceAll('_', ' ')}</label><input className="input w-24" type="number" step="0.1" min="0" value={w[`weight_${s}`] ?? 1} onChange={(e) => setW({ ...w, [`weight_${s}`]: e.target.value })} /></div>)}
        <button className="btn" onClick={() => save()}>Save weights</button></div>
      <div className="card md:col-span-2"><h2 className="font-semibold mb-2">Working days & periods</h2><div className="grid grid-cols-2 md:grid-cols-7 gap-3">
        {[['days', 'Days (1-6)'], ['periods', 'Periods/day'], ['first_start', 'First start'], ['period_minutes', 'Period min'], ['gap_minutes', 'Gap min'], ['break_after_period', 'Lunch after period idx (-1 none)'], ['lunch_minutes', 'Lunch min']].map(([k, l]) => <div key={k}><label className="label">{l}</label><input className="input" value={cfg[k]} onChange={(e) => setCfg({ ...cfg, [k]: e.target.value })} /></div>)}</div>
        <button className="btn mt-3" onClick={saveSlots}>Apply period grid</button>
        <p className="text-xs text-slate-500 mt-2">Current: {slots ? `${new Set(slots.slots.map((s) => s.day)).size} days × ${new Set(slots.slots.map((s) => s.period)).size} periods, lunch after period index ${slots.break_after_period}` : ''}. Regenerate timetables after changing the grid.</p></div></div></div>
}

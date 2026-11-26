import { useEffect, useState } from 'react'
import api, { errMsg, download } from '../services/api'
import { useAuth } from '../context/AuthContext'
import TimetableGrid from '../components/TimetableGrid'
import { Alert, VersionSelect, useLoad } from '../components/ui'

export default function TimetableView() {
  const { user } = useAuth(); const [vid, setVid] = useState(null); const [f, setF] = useState({}); const [view, setView] = useState('weekly')
  const [data, setData] = useState(null); const [err, setErr] = useState('')
  const staff = user.role === 'admin' || user.role === 'hod'
  const [depts] = useLoad(staff ? '/departments' : null); const [secs] = useLoad(staff ? '/sections' : null)
  const [facs] = useLoad(staff ? '/faculty' : null); const [rooms] = useLoad(staff ? '/rooms' : null)
  useEffect(() => { if (!vid) return; const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v)); api.get(`/timetable/${vid}?${p}`).then((r) => { setData(r.data); setErr('') }).catch((e) => setErr(errMsg(e))) }, [vid, f])
  const sel = (k, label, list, lab) => <div><label className="label">{label}</label><select className="input" value={f[k] || ''} onChange={(e) => setF({ ...f, [k]: e.target.value })}><option value="">All</option>{(list || []).map((x) => <option key={x.id} value={x.id}>{lab(x)}</option>)}</select></div>
  return <div><h1 className="h1">{user.role === 'student' ? 'My Section Timetable' : user.role === 'faculty' ? 'My Timetable' : 'Timetable'}</h1>
    <div className="card mb-4 grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
      <div className="col-span-2"><label className="label">Version</label><VersionSelect value={vid} onChange={setVid} /></div>
      {staff && sel('department_id', 'Department', depts, (d) => d.code)}
      {staff && <div><label className="label">Semester</label><input className="input" type="number" min="1" value={f.semester || ''} onChange={(e) => setF({ ...f, semester: e.target.value })} /></div>}
      {staff && sel('section_id', 'Section', secs, (s) => `${s.name} (dept ${s.department_id}, sem ${s.semester})`)}
      {staff && sel('faculty_id', 'Faculty', facs, (x) => x.full_name)}
      {staff && sel('room_id', 'Room', rooms, (r) => r.name)}
      <div><label className="label">View</label><select className="input" value={view} onChange={(e) => setView(e.target.value)}><option value="weekly">Weekly</option><option value="daily">Daily</option></select></div>
    </div>
    <Alert kind="error">{err}</Alert>
    {data && <>
      <div className="flex justify-between items-center mb-2"><div className="text-sm text-slate-500">{data.version.name} · status <b>{data.version.status}</b> · hard violations {data.version.hard_violations}</div>
        <div className="space-x-2"><button className="btn-ghost" onClick={() => download(`/export/timetable/${vid}/pdf`, `timetable_${vid}.pdf`)}>PDF</button>{user.role !== 'student' && <button className="btn-ghost" onClick={() => download(`/export/timetable/${vid}/excel`, `timetable_${vid}.xlsx`)}>Excel</button>}</div></div>
      <TimetableGrid entries={data.entries} grid={data.grid} view={view} showSection={user.role !== 'student'} /></>}
    {!data && !err && <div className="text-slate-500">No timetable available yet.</div>}</div>
}

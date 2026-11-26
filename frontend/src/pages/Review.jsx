import { useEffect, useState } from 'react'
import api, { errMsg } from '../services/api'
import TimetableGrid from '../components/TimetableGrid'
import { Alert, Table, VersionSelect, useLoad, DAYS } from '../components/ui'

export function Conflicts() {
  const [vid, setVid] = useState(null); const [d, setD] = useState(null); const [err, setErr] = useState('')
  useEffect(() => { if (vid) api.get(`/timetable/${vid}/conflicts`).then((r) => { setD(r.data); setErr('') }).catch((e) => setErr(errMsg(e))) }, [vid])
  return <div><h1 className="h1">Conflict Reports</h1><div className="card mb-4"><VersionSelect value={vid} onChange={setVid} /></div><Alert kind="error">{err}</Alert>
    {d && (d.hard_violation_count === 0 ? <Alert kind="ok">No hard-constraint violations. This timetable is publishable.</Alert> : <Alert kind="error">{d.hard_violation_count} hard violation(s) – this timetable cannot be published.</Alert>)}
    {d && d.violations.length > 0 && <div className="card p-0"><Table cols={[{ key: 'type', label: 'Violation' }, { key: 'faculty', label: 'Faculty' }, { key: 'subject', label: 'Subject' }, { key: 'section', label: 'Section' }, { key: 'room', label: 'Room' }, { key: 'slot', label: 'Day / period' }, { key: 'explanation', label: 'Explanation' }, { key: 'suggestion', label: 'Suggested action' }]} rows={d.violations} /></div>}</div>
}

export function ManualEdit() {
  const [vid, setVid] = useState(null); const [data, setData] = useState(null); const [sec, setSec] = useState(''); const [sel, setSel] = useState(null)
  const [rooms] = useLoad('/rooms'); const [secs] = useLoad('/sections'); const [form, setForm] = useState({}); const [err, setErr] = useState(''); const [viol, setViol] = useState([]); const [ok, setOk] = useState('')
  const load = () => vid && api.get(`/timetable/${vid}${sec ? `?section_id=${sec}` : ''}`).then((r) => setData(r.data)).catch((e) => setErr(errMsg(e)))
  useEffect(() => { load() }, [vid, sec])
  const pick = (e) => { setSel(e); setForm({ day: e.day, period: e.period, room_id: e.room_id }); setViol([]); setErr(''); setOk('') }
  const clone = async () => { const r = await api.post(`/timetable/${vid}/clone`); setOk(`Created editable copy #${r.data.version_id}`); setVid(r.data.version_id) }
  const save = async () => { setErr(''); setViol([]); setOk(''); try { await api.put(`/timetable/${vid}`, { entry_id: sel.id, day: +form.day, period: +form.period, room_id: +form.room_id }); setOk('Saved – validator found no hard violations.'); setSel(null); load() } catch (e) { setErr(errMsg(e)); setViol(e.response?.data?.detail?.violations || []) } }
  const editable = data && ['draft', 'rejected'].includes(data.version.status)
  return <div><h1 className="h1">Manual Timetable Editing</h1><p className="text-sm text-slate-500 mb-3">Every change is validated against all hard constraints before it is saved.</p>
    <div className="card mb-4 flex gap-3 items-end"><div><label className="label">Version</label><VersionSelect value={vid} onChange={setVid} /></div>
      <div><label className="label">Section</label><select className="input" value={sec} onChange={(e) => setSec(e.target.value)}><option value="">All</option>{(secs || []).map((s) => <option key={s.id} value={s.id}>{s.name} (dept {s.department_id})</option>)}</select></div>
      {data && !editable && <button className="btn" onClick={clone}>Clone to edit ({data.version.status})</button>}</div>
    <Alert kind="error">{err}</Alert><Alert kind="ok">{ok}</Alert>
    {viol.length > 0 && <div className="card mb-3 p-0"><Table cols={[{ key: 'type', label: 'Violation' }, { key: 'explanation', label: 'Explanation' }, { key: 'suggestion', label: 'Suggestion' }]} rows={viol} /></div>}
    {sel && editable && <div className="card mb-3 flex flex-wrap gap-3 items-end"><b>{sel.subject} — {sel.section}</b>
      <div><label className="label">Day</label><select className="input" value={form.day} onChange={(e) => setForm({ ...form, day: e.target.value })}>{DAYS.slice(0, data.grid.days).map((n, i) => <option key={n} value={i}>{n}</option>)}</select></div>
      <div><label className="label">Period</label><select className="input" value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })}>{data.grid.periods.map((p) => <option key={p.period} value={p.period}>P{p.period + 1}</option>)}</select></div>
      <div><label className="label">Room</label><select className="input" value={form.room_id} onChange={(e) => setForm({ ...form, room_id: e.target.value })}>{(rooms || []).map((r) => <option key={r.id} value={r.id}>{r.name} ({r.capacity}{r.is_lab ? ', lab' : ''})</option>)}</select></div>
      <button className="btn" onClick={save}>Validate & save</button></div>}
    {data && <TimetableGrid entries={data.entries} grid={data.grid} onSelect={editable ? pick : undefined} selectedId={sel?.id} />}</div>
}

export function Reopt() {
  const [me] = useLoad('/auth/me'); const [vid, setVid] = useState(null); const [type, setType] = useState('faculty'); const [target, setTarget] = useState('')
  const [facs] = useLoad('/faculty'); const [rooms] = useLoad('/rooms'); const [sl, setSl] = useState({}); const [whole, setWhole] = useState(false); const [persist, setPersist] = useState(false)
  const [res, setRes] = useState(null); const [err, setErr] = useState(''); const [slots] = useLoad('/config/timeslots'); const hod = me?.role === 'hod'
  const periods = slots ? [...new Set(slots.slots.map((s) => s.period))] : []; const days = slots ? Math.max(...slots.slots.map((s) => s.day)) + 1 : 5
  const submit = async () => { setErr(''); setRes(null)
    const body = { version_id: vid, event_type: type, persist, slots: whole ? null : Object.keys(sl).filter((k) => sl[k]).map((k) => { const [day, period] = k.split('-').map(Number); return { day, period } }) }
    if (type === 'faculty') body.faculty_id = +target; else body.room_id = +target
    if (!whole && !body.slots.length) { setErr('Select at least one period or tick "whole week".'); return }
    try { const r = await api.post('/reoptimization/request', body); setRes(r.data) } catch (e) { setErr(errMsg(e)) } }
  return <div><h1 className="h1">{hod ? 'Request Incremental Re-optimization' : 'Incremental Re-optimization'}</h1>
    <p className="text-sm text-slate-500 mb-3">Only the affected classes (and, if needed, their dependent neighbours) are re-planned; everything else stays locked.</p>
    <div className="card mb-4 grid md:grid-cols-4 gap-3"><div><label className="label">Base timetable</label><VersionSelect value={vid} onChange={setVid} /></div>
      <div><label className="label">Event</label><select className="input" value={type} onChange={(e) => { setType(e.target.value); setTarget('') }}><option value="faculty">Faculty unavailable</option>{!hod && <option value="room">Classroom unavailable</option>}</select></div>
      <div><label className="label">{type === 'faculty' ? 'Faculty' : 'Room'}</label><select className="input" value={target} onChange={(e) => setTarget(e.target.value)}><option value="">Select…</option>{(type === 'faculty' ? facs || [] : rooms || []).map((x) => <option key={x.id} value={x.id}>{x.full_name || x.name}</option>)}</select></div>
      <div className="flex items-end gap-4"><label className="text-sm"><input type="checkbox" checked={whole} onChange={(e) => setWhole(e.target.checked)} /> Whole week</label>{!hod && <label className="text-sm"><input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} /> Save as permanent</label>}</div>
      {!whole && <div className="md:col-span-4 overflow-x-auto"><table className="text-sm"><thead><tr><th></th>{DAYS.slice(0, days).map((d) => <th key={d} className="px-2">{d}</th>)}</tr></thead><tbody>{periods.map((p) => <tr key={p}><td className="pr-2">P{p + 1}</td>{Array.from({ length: days }).map((_, d) => <td key={d} className="text-center"><input type="checkbox" checked={!!sl[`${d}-${p}`]} onChange={(e) => setSl({ ...sl, [`${d}-${p}`]: e.target.checked })} /></td>)}</tr>)}</tbody></table></div>}
      <div><button className="btn" disabled={!vid || !target} onClick={submit}>{hod ? 'Send request to admin' : 'Run re-optimization'}</button></div></div>
    <Alert kind="error">{err}</Alert>
    {res?.status === 'pending_admin' && <Alert kind="ok">Request #{res.change_request_id} sent to the administrator.</Alert>}
    {res && res.success !== undefined && <div className="card"><Alert kind={res.success ? 'ok' : 'error'}>{res.success ? 'Repair succeeded.' : 'Repair failed – the published timetable is unchanged.'} {res.reason}</Alert>
      <div className="text-sm mb-2">Affected: <b>{res.affected.length}</b> · Re-planned (unlocked): <b>{res.unlocked_count}</b> · Changed: <b>{res.changed_count}</b> · Expansion level: <b>{res.expansion_level}</b>{res.new_version_id && <> · New draft version <b>#{res.new_version_id}</b> (original #{res.original_version_id} preserved)</>}</div>
      <Table cols={[{ key: 'subject', label: 'Subject' }, { key: 'section', label: 'Section' }, { key: 'faculty', label: 'Faculty' }, { key: 'room', label: 'Room' }, { key: 'slot', label: 'Was at' }]} rows={res.affected} />
      {res.suggestions?.length > 0 && <div className="mt-3"><b className="text-sm">Suggested alternatives</b><ul className="list-disc ml-5 text-sm">{res.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul></div>}</div>}</div>
}

import { useState } from 'react'
import api, { errMsg } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Alert, Badge, Table, useLoad, DAYS } from '../components/ui'

export default function Requests() {
  const { user } = useAuth(); const [leaves, , rl] = useLoad(user.role !== 'student' ? '/leave-requests' : null); const [crs, , rc] = useLoad('/change-requests')
  const [lf, setLf] = useState({ day: 0, period_from: 0, period_to: 99, reason: '' }); const [desc, setDesc] = useState(''); const [msg, setMsg] = useState(''); const [err, setErr] = useState(''); const [note, setNote] = useState('')
  const run = async (fn, ok) => { setErr(''); setMsg(''); try { await fn(); setMsg(ok); rl(); rc() } catch (e) { setErr(errMsg(e)) } }
  return <div><h1 className="h1">Leave & Change Requests</h1><Alert kind="error">{err}</Alert><Alert kind="ok">{msg}</Alert>
    {user.role === 'faculty' && <div className="grid md:grid-cols-2 gap-4 mb-4">
      <div className="card space-y-2"><b>Submit leave / unavailability</b>
        <div className="grid grid-cols-3 gap-2"><div><label className="label">Day</label><select className="input" value={lf.day} onChange={(e) => setLf({ ...lf, day: +e.target.value })}>{DAYS.slice(0, 5).map((d, i) => <option key={d} value={i}>{d}</option>)}</select></div>
          <div><label className="label">From period</label><input className="input" type="number" min="0" value={lf.period_from} onChange={(e) => setLf({ ...lf, period_from: +e.target.value })} /></div>
          <div><label className="label">To period</label><input className="input" type="number" min="0" value={lf.period_to} onChange={(e) => setLf({ ...lf, period_to: +e.target.value })} /></div></div>
        <input className="input" placeholder="Reason" value={lf.reason} onChange={(e) => setLf({ ...lf, reason: e.target.value })} /><button className="btn" onClick={() => run(() => api.post('/leave-requests', lf), 'Leave request submitted')}>Submit</button></div>
      <div className="card space-y-2"><b>Request a timetable modification</b><textarea className="input" rows="3" placeholder="Describe the change you need" value={desc} onChange={(e) => setDesc(e.target.value)} /><button className="btn" onClick={() => run(() => api.post('/change-requests', { description: desc }), 'Request sent')}>Send</button></div></div>}
    {user.role !== 'student' && <div className="card p-0 mb-4"><div className="p-3 font-semibold">Leave requests</div><Table cols={[{ key: 'faculty_id', label: 'Faculty ID' }, { label: 'Day', render: (l) => DAYS[l.day] }, { label: 'Periods', render: (l) => `${l.period_from + 1}–${l.period_to >= 99 ? 'end' : l.period_to + 1}` }, { key: 'reason', label: 'Reason' }, { label: 'Status', render: (l) => <Badge v={l.status} /> },
      { label: '', render: (l) => user.role !== 'faculty' && l.status === 'pending' && <span className="space-x-2"><button className="btn" onClick={() => run(() => api.post(`/leave-requests/${l.id}/approve`), 'Approved')}>Approve</button><button className="btn-danger" onClick={() => run(() => api.post(`/leave-requests/${l.id}/reject`), 'Rejected')}>Reject</button></span> }]} rows={leaves || []} /></div>}
    <div className="card p-0"><div className="p-3 font-semibold">Change requests</div>{user.role === 'admin' && <div className="px-3 pb-2"><input className="input" placeholder="Response note" value={note} onChange={(e) => setNote(e.target.value)} /></div>}
      <Table cols={[{ key: 'id', label: '#' }, { key: 'request_type', label: 'Type' }, { key: 'description', label: 'Description' }, { label: 'Status', render: (c) => <Badge v={c.status} /> }, { key: 'response_note', label: 'Response' },
        { label: '', render: (c) => user.role === 'admin' && c.status === 'pending' && <button className="btn-ghost" onClick={() => run(() => api.post(`/change-requests/${c.id}/resolve`, { comment: note }), 'Resolved')}>Mark resolved</button> }]} rows={crs || []} /></div></div>
}

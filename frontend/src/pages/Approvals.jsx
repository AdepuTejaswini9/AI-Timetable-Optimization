import { useState } from 'react'
import api, { errMsg } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Alert, Badge, Table, useLoad } from '../components/ui'

export default function Approvals() {
  const { user } = useAuth(); const admin = user.role === 'admin'
  const [versions, , rv] = useLoad('/timetable'); const [apps, , ra] = useLoad('/approvals'); const [depts] = useLoad('/departments')
  const [msg, setMsg] = useState(''); const [err, setErr] = useState(''); const [comment, setComment] = useState('')
  const reload = () => { rv(); ra() }
  const run = async (fn, ok) => { setErr(''); setMsg(''); try { await fn(); setMsg(ok); reload() } catch (e) { setErr(errMsg(e)) } }
  const dname = (id) => (depts || []).find((d) => d.id === id)?.code || id
  const vname = (id) => (versions || []).find((v) => v.id === id)?.name || `#${id}`
  return <div><h1 className="h1">{admin ? 'Approvals & Publication' : 'Timetable Approvals'}</h1><Alert kind="error">{err}</Alert><Alert kind="ok">{msg}</Alert>
    {admin && <div className="card mb-4 p-0"><Table cols={[{ key: 'id', label: '#' }, { key: 'name', label: 'Name' }, { label: 'Status', render: (v) => <Badge v={v.status} /> }, { key: 'version_number', label: 'Ver' }, { key: 'hard_violations', label: 'Hard viol.' }, { label: 'Actions', render: (v) => <span className="space-x-2">
      {['draft', 'rejected'].includes(v.status) && <button className="btn-ghost" onClick={() => run(() => api.post('/approvals/submit', { version_id: v.id }), 'Submitted to HODs')}>Submit for approval</button>}
      {v.status === 'approved' && <button className="btn" onClick={() => run(() => api.post(`/timetable/${v.id}/publish`), 'Published')}>Publish</button>}</span> }]} rows={versions || []} /></div>}
    <div className="card p-0"><div className="p-3 font-semibold">Department approval records</div>
      {!admin && <div className="px-3 pb-3"><input className="input" placeholder="Comment (optional)" value={comment} onChange={(e) => setComment(e.target.value)} /></div>}
      <Table cols={[{ key: 'id', label: '#' }, { label: 'Timetable', render: (a) => vname(a.version_id) }, { label: 'Dept', render: (a) => dname(a.department_id) }, { label: 'Status', render: (a) => <Badge v={a.status} /> }, { key: 'comment', label: 'Comment' },
        { label: '', render: (a) => a.status === 'pending' && <span className="space-x-2"><button className="btn" onClick={() => run(() => api.post(`/approvals/${a.id}/approve`, { comment }), 'Approved')}>Approve</button><button className="btn-danger" onClick={() => run(() => api.post(`/approvals/${a.id}/reject`, { comment }), 'Rejected')}>Reject</button></span> }]} rows={apps || []} /></div></div>
}

import { useState } from 'react'
import api, { errMsg } from '../services/api'
import { Alert, Table, useLoad } from './ui'

/** Generic CRUD page. fields: [{key,label,type:'text|number|password|checkbox|select',options:[{value,label}]|optionsUrl}] */
export default function CrudPage({ title, path, fields, columns, canWrite = true, defaults = {} }) {
  const [rows, err, reload] = useLoad(path)
  const [form, setForm] = useState(null); const [msg, setMsg] = useState(''); const [error, setError] = useState('')
  const [opts, setOpts] = useState({})
  const loadOpts = async () => {
    const o = {}
    for (const f of fields) if (f.optionsUrl) { const r = await api.get(f.optionsUrl); o[f.key] = r.data.map((x) => ({ value: x.id, label: f.optionLabel(x) })) }
    setOpts(o)
  }
  const open = async (row) => { await loadOpts(); setError(''); setForm(row ? { ...row, password: '' } : { ...defaults }) }
  const save = async (e) => {
    e.preventDefault(); setError('')
    const body = {}; fields.forEach((f) => { let v = form[f.key]; if (f.type === 'number' || f.optionsUrl) v = v === '' || v == null ? undefined : Number(v); if (f.type === 'password' && !v) v = undefined; body[f.key] = v })
    try { form.id ? await api.put(`${path}/${form.id}`, body) : await api.post(path, body); setForm(null); setMsg('Saved'); reload() } catch (x) { setError(errMsg(x)) }
  }
  const del = async (r) => { if (!confirm('Delete this record?')) return; try { await api.delete(`${path}/${r.id}`); setMsg('Deleted'); reload() } catch (x) { setError(errMsg(x)) } }
  const cols = [...columns, ...(canWrite ? [{ label: 'Actions', render: (r) => <span className="space-x-2"><button className="btn-ghost" onClick={() => open(r)}>Edit</button><button className="btn-danger" onClick={() => del(r)}>Delete</button></span> }] : [])]
  return (
    <div>
      <div className="flex items-center justify-between"><h1 className="h1">{title}</h1>{canWrite && <button className="btn" onClick={() => open(null)}>+ Add</button>}</div>
      <Alert kind="error">{err || error}</Alert><Alert kind="ok">{msg}</Alert>
      {form && <form onSubmit={save} className="card mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        {fields.map((f) => <div key={f.key}><label className="label">{f.label}</label>
          {f.type === 'checkbox' ? <input type="checkbox" checked={!!form[f.key]} onChange={(e) => setForm({ ...form, [f.key]: e.target.checked })} />
            : f.optionsUrl || f.options ? <select className="input" required={!f.optional} value={form[f.key] ?? ''} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}><option value="">Select…</option>{(f.options || opts[f.key] || []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
              : <input className="input" type={f.type || 'text'} required={!f.optional && !(f.type === 'password' && form.id)} placeholder={f.type === 'password' && form.id ? 'leave blank to keep' : ''} value={form[f.key] ?? ''} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />}</div>)}
        <div className="md:col-span-3 flex gap-2"><button className="btn">Save</button><button type="button" className="btn-ghost" onClick={() => setForm(null)}>Cancel</button></div></form>}
      <div className="card p-0"><Table cols={cols} rows={rows || []} /></div>
    </div>)
}

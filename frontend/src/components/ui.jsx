import { useEffect, useState } from 'react'
import api, { errMsg } from '../services/api'

export const Stat = ({ label, value }) => <div className="card"><div className="text-xs uppercase text-slate-500 font-semibold">{label}</div><div className="text-3xl font-semibold text-navy-800 mt-1">{value ?? '-'}</div></div>
export const Alert = ({ kind = 'info', children }) => !children ? null : <div className={`rounded-lg px-3 py-2 text-sm mb-3 ${kind === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : kind === 'ok' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-blue-50 text-blue-800 border border-blue-200'}`}>{children}</div>
const COL = { published: 'bg-green-100 text-green-800', approved: 'bg-emerald-100 text-emerald-800', pending: 'bg-amber-100 text-amber-800', draft: 'bg-slate-100 text-slate-700', rejected: 'bg-red-100 text-red-700', archived: 'bg-slate-200 text-slate-500', completed: 'bg-green-100 text-green-800', running: 'bg-blue-100 text-blue-800', failed: 'bg-red-100 text-red-700' }
export const Badge = ({ v }) => <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${COL[v] || 'bg-slate-100 text-slate-700'}`}>{v}</span>
export const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function useLoad(url, deps = []) {
  const [data, setData] = useState(null); const [error, setError] = useState(''); const [tick, setTick] = useState(0)
  useEffect(() => { if (!url) return; api.get(url).then((r) => { setData(r.data); setError('') }).catch((e) => setError(errMsg(e))) }, [url, tick, ...deps])
  return [data, error, () => setTick((t) => t + 1)]
}

export function VersionSelect({ value, onChange, filter }) {
  const [vs] = useLoad('/timetable')
  const list = (vs || []).filter(filter || (() => true))
  useEffect(() => { if (!value && list.length) onChange(list[0].id) }, [vs])
  return <select className="input max-w-xs" value={value || ''} onChange={(e) => onChange(Number(e.target.value))}>
    {list.map((v) => <option key={v.id} value={v.id}>#{v.id} {v.name} [{v.status}]</option>)}</select>
}

export function Table({ cols, rows, empty = 'No records' }) {
  return <div className="overflow-x-auto"><table className="min-w-full"><thead><tr>{cols.map((c) => <th key={c.key || c.label} className="th">{c.label}</th>)}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={r.id ?? i} className="hover:bg-slate-50">{cols.map((c) => <td key={c.key || c.label} className="td">{c.render ? c.render(r) : String(r[c.key] ?? '')}</td>)}</tr>)}
      {!rows.length && <tr><td className="td text-slate-400" colSpan={cols.length}>{empty}</td></tr>}</tbody></table></div>
}

import { useState } from 'react'
import { DAYS } from './ui'

export default function TimetableGrid({ entries, grid, onSelect, selectedId, showSection = true, view = 'weekly' }) {
  const [day, setDay] = useState(0)
  const days = grid?.days || 5; const periods = grid?.periods || []
  const cellsFor = (d, p) => entries.filter((e) => e.day === d && e.period <= p && p < e.period + e.duration).map((e) => ({ e, cont: e.period !== p }))
  const Card = ({ e, cont }) => (
    <div onClick={() => onSelect && onSelect(e)} className={`rounded-md border px-2 py-1 text-xs mb-1 ${onSelect ? 'cursor-pointer' : ''} ${selectedId === e.id ? 'ring-2 ring-navy-600' : ''} ${e.is_lab ? 'bg-violet-50 border-violet-200' : 'bg-navy-50 border-navy-100'}`}>
      <div className="font-semibold text-navy-900">{cont ? '↳ ' : ''}{e.subject}{e.is_lab && <span className="ml-1 rounded bg-violet-600 text-white px-1 text-[10px]">LAB</span>}</div>
      {!cont && <div className="text-slate-600">{e.faculty}{showSection && e.section ? ` · ${e.section}` : ''}</div>}
      {!cont && <div className="text-slate-500">Room {e.room}</div>}
    </div>)
  if (view === 'daily') return (
    <div>
      <div className="flex gap-2 mb-3">{DAYS.slice(0, days).map((n, i) => <button key={n} className={i === day ? 'btn' : 'btn-ghost'} onClick={() => setDay(i)}>{n}</button>)}</div>
      <div className="space-y-2">{periods.map((pr) => <div key={pr.period} className="card flex gap-3"><div className="w-28 text-sm text-slate-500">P{pr.period + 1}<br />{pr.start}–{pr.end}</div>
        <div className="flex-1">{cellsFor(day, pr.period).map((c, i) => <Card key={i} {...c} />)}{!cellsFor(day, pr.period).length && <span className="text-slate-300 text-sm">Free</span>}</div></div>)}</div>
    </div>)
  return (
    <div className="overflow-x-auto"><table className="min-w-full border-collapse bg-white rounded-xl overflow-hidden">
      <thead><tr><th className="th w-28">Period</th>{DAYS.slice(0, days).map((n) => <th key={n} className="th">{n}</th>)}</tr></thead>
      <tbody>{periods.map((pr) => <tr key={pr.period}><td className="td bg-slate-50 text-xs text-slate-500 whitespace-nowrap">P{pr.period + 1}<br />{pr.start}–{pr.end}</td>
        {Array.from({ length: days }).map((_, d) => <td key={d} className="td align-top min-w-[150px] border-l">{cellsFor(d, pr.period).map((c, i) => <Card key={i} {...c} />)}</td>)}</tr>)}</tbody></table></div>)
}

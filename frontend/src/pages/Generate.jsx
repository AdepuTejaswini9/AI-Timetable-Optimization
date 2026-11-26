import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'
import api, { errMsg } from '../services/api'
import { Alert, Badge, Table, useLoad } from '../components/ui'
const OBJ = ['student_free_periods', 'faculty_preference_violations', 'excess_consecutive_teaching', 'room_underutilization', 'subject_distribution']

export default function Generate() {
  const [f, setF] = useState({ algorithm: 'nsga2_ls', population: 40, generations: 40, ls_iterations: 150, seed: 1 })
  const [runId, setRunId] = useState(null); const [run, setRun] = useState(null); const [err, setErr] = useState(''); const timer = useRef()
  const [runs, , reloadRuns] = useLoad('/optimization')
  const poll = (id) => { clearInterval(timer.current); timer.current = setInterval(async () => { try { const r = await api.get(`/optimization/${id}/status`); setRun(r.data); if (['completed', 'failed'].includes(r.data.status)) { clearInterval(timer.current); reloadRuns() } } catch (e) { setErr(errMsg(e)); clearInterval(timer.current) } }, 1000) }
  useEffect(() => () => clearInterval(timer.current), [])
  const start = async (e) => { e.preventDefault(); setErr(''); setRun(null); try { const r = await api.post('/optimization/generate', { ...f, population: +f.population, generations: +f.generations, ls_iterations: +f.ls_iterations, seed: +f.seed }); setRunId(r.data.run_id); poll(r.data.run_id) } catch (x) { setErr(errMsg(x)) } }
  const p = run?.progress; const hist = run?.history || []
  const pct = p ? Math.round((p.generation / p.total_generations) * 100) : 0
  return <div><h1 className="h1">Generate / Optimize Timetable</h1><Alert kind="error">{err}</Alert>
    <form onSubmit={start} className="card grid grid-cols-2 md:grid-cols-6 gap-3 items-end mb-4">
      <div className="col-span-2"><label className="label">Algorithm</label><select className="input" value={f.algorithm} onChange={(e) => setF({ ...f, algorithm: e.target.value })}><option value="ga">Genetic Algorithm (baseline, single objective)</option><option value="nsga2">NSGA-II (Pareto)</option><option value="nsga2_ls">NSGA-II + Local Search (hybrid)</option></select></div>
      {[['population', 'Population'], ['generations', 'Generations'], ['ls_iterations', 'LS iterations'], ['seed', 'Seed']].map(([k, l]) => <div key={k}><label className="label">{l}</label><input className="input" type="number" min="1" value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></div>)}
      <button className="btn md:col-span-6 w-40">Run optimization</button></form>
    {run && <div className="card mb-4"><div className="flex items-center gap-3 mb-2"><b>Run #{run.id}</b><Badge v={run.status} />{run.outcome && <Badge v={run.outcome} />}<span className="text-sm text-slate-500">{run.algorithm}</span></div>
      <div className="h-2 bg-slate-100 rounded mb-3"><div className="h-2 bg-navy-700 rounded" style={{ width: `${run.status === 'completed' ? 100 : pct}%` }} /></div>
      {p && <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm mb-3"><div>Generation <b>{p.generation}/{p.total_generations}</b></div><div>Candidates <b>{p.candidates}</b></div><div>Best hard violations <b>{p.best_hard}</b></div><div>Gen time <b>{p.duration_s}s</b></div>{p.pareto_size != null && <div>Pareto size <b>{p.pareto_size}</b></div>}</div>}
      {p?.best_objectives?.length > 0 && <div className="text-sm mb-3">Soft objectives: {OBJ.map((o, i) => <span key={o} className="mr-3">{o.replaceAll('_', ' ')} <b>{p.best_objectives[i]}</b></span>)}</div>}
      {hist.length > 1 && <div className="h-56"><ResponsiveContainer><LineChart data={hist.map((h) => ({ gen: h.generation, objective_sum: h.best_objectives?.reduce((a, b) => a + b, 0), hard: h.best_hard }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="gen" /><YAxis /><Tooltip /><Legend /><Line type="monotone" dataKey="objective_sum" stroke="#1e3a8a" dot={false} /><Line type="monotone" dataKey="hard" stroke="#dc2626" dot={false} /></LineChart></ResponsiveContainer></div>}
      {run.message && <Alert kind={run.outcome === 'feasible_found' ? 'ok' : run.status === 'completed' ? 'error' : 'info'}>{run.message}</Alert>}
      {run.violations?.length > 0 && <Table cols={[{ key: 'type', label: 'Type' }, { key: 'explanation', label: 'Explanation' }, { key: 'suggestion', label: 'Suggestion' }]} rows={run.violations} />}
      {run.outcome === 'feasible_found' && <Link className="btn mt-3" to={`/solutions?run=${run.id}`}>Compare solutions →</Link>}</div>}
    <div className="card"><h2 className="font-semibold mb-2">Optimization history (algorithm comparison)</h2>
      <Table cols={[{ key: 'id', label: 'Run' }, { key: 'algorithm', label: 'Algorithm' }, { label: 'Status', render: (r) => <Badge v={r.status} /> }, { key: 'outcome', label: 'Outcome' }, { label: 'Generations', render: (r) => r.progress?.generation ?? '' }, { label: 'Best objectives', render: (r) => r.progress?.best_objectives?.join(', ') }, { label: '', render: (r) => r.outcome === 'feasible_found' && <Link className="text-navy-700 underline" to={`/solutions?run=${r.id}`}>Solutions</Link> }]} rows={(runs || []).filter((r) => r.algorithm !== 'incremental')} /></div></div>
}

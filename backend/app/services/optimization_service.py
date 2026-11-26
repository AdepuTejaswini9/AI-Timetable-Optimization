"""Runs optimisation jobs against the database (used by background tasks and synchronous endpoints)."""
import time
from datetime import datetime
import numpy as np
from app.database.session import SessionLocal
from app.models import *
from app.algorithms.problem import OBJ_NAMES
from app.algorithms.explain import describe, proof_of_infeasibility
from app.algorithms.ga import run_ga
from app.algorithms.nsga2 import run_nsga2
from app.algorithms.local_search import improve_front
from app.services.data_loader import build_problem, create_version

def _save_violations(db, run_id, items):
    for v in items:
        db.add(ConstraintViolation(run_id=run_id, type=v["type"], severity=v.get("severity", "hard"),
               faculty_id=v.get("faculty_id"), subject_id=v.get("subject_id"), section_id=v.get("section_id"),
               room_id=v.get("room_id"), day=v.get("day"), period=v.get("period"),
               explanation=v["explanation"], suggestion=v.get("suggestion")))

def _spread(front, k):
    front = sorted(front, key=lambda x: float(np.sum(x[1])))
    if len(front) <= k: return front
    return [front[i] for i in np.linspace(0, len(front) - 1, k).astype(int)]

def execute_run(run_id: int):
    db = SessionLocal()
    try:
        run = db.get(OptimizationRun, run_id); P = run.params
        run.status = "running"; db.commit()
        prob = build_problem(db); hist = []
        reasons = proof_of_infeasibility(prob)
        if reasons:
            _save_violations(db, run_id, reasons)
            run.status, run.outcome = "completed", "proven_infeasible"
            run.message = "PROVEN INFEASIBLE: " + " | ".join(r["explanation"] for r in reasons[:3])
            run.finished_at = datetime.utcnow(); db.commit(); return
        def cb(rec):
            hist.append(rec)
            run.progress = {**rec, "total_generations": P["generations"], "algorithm": run.algorithm}
            if rec["generation"] % 3 == 0 or rec["generation"] == P["generations"]:
                run.history = list(hist); db.commit()
        front, best_inf = [], None
        if run.algorithm == "ga":
            r = run_ga(prob, P["population"], P["generations"], seed=P["seed"], callback=cb)
            g, h, o = r["best"]
            if h == 0: front = [(g, o)]
            else: best_inf = (g, h, o)
        else:
            r = run_nsga2(prob, P["population"], P["generations"], seed=P["seed"], callback=cb)
            front, best_inf = r["front"], r["best_infeasible"]
            if run.algorithm == "nsga2_ls" and front and P["ls_iterations"] > 0:
                front = improve_front(prob, front, P["ls_iterations"], P["seed"])
        run.history = hist
        if front:
            for rank, (g, o) in enumerate(_spread(front, 12)):
                db.add(OptimizationSolution(run_id=run_id, rank=rank, genes=np.asarray(g).astype(int).tolist(),
                       objectives=dict(zip(OBJ_NAMES, [float(x) for x in o])), hard_violations=0))
            run.outcome = "feasible_found"
            run.message = f"{min(len(front), 12)} feasible alternative(s) stored."
        else:
            g, h, o = best_inf
            _save_violations(db, run_id, describe(prob, g))
            run.outcome = "search_limit_reached"
            run.message = (f"No feasible timetable found within the search limit (best candidate still has {h} hard "
                           "violation(s)). This is NOT a proof of infeasibility – increase population/generations.")
        run.status = "completed"; run.finished_at = datetime.utcnow(); db.commit()
    except Exception as e:  # noqa
        db.rollback(); run = db.get(OptimizationRun, run_id)
        run.status, run.message, run.finished_at = "failed", f"Internal error: {type(e).__name__}", datetime.utcnow(); db.commit()
    finally:
        db.close()

def select_solution(db, run, sol, user_id, name=None):
    prob = build_problem(db)
    genes = np.array(sol.genes, dtype=int)
    if prob.hard_count(genes) != 0:
        raise ValueError("Solution is no longer feasible for the current data; regenerate.")
    v = create_version(db, prob, genes, name or f"Run {run.id} / solution {sol.rank + 1}", run_id=run.id, user_id=user_id)
    for s in db.query(OptimizationSolution).filter_by(run_id=run.id): s.is_selected = (s.id == sol.id)
    sol.version_id = v.id; db.commit(); return v

"""Hill-climbing local search over feasible timetables. Accepts a neighbour only if it is hard-feasible and
Pareto-dominates the current solution on the soft-objective vector."""
import random
import numpy as np
from app.algorithms.nsga2 import dominates, pareto_filter

def hill_climb(prob, genes, iterations=200, seed=1):
    rng = random.Random(seed)
    cur = np.array(genes, dtype=int).reshape(-1, 3)
    h, obj = prob.evaluate(cur)
    if h != 0: raise ValueError("Local search requires a feasible timetable")
    accepted = 0
    for _ in range(iterations):
        nb = prob.neighbors_move(cur, rng)
        if nb is None: continue
        h2, o2 = prob.evaluate(nb)
        if h2 == 0 and dominates(o2, obj):
            cur, obj, accepted = nb, o2, accepted + 1
    return cur, obj, accepted

def improve_front(prob, front, iterations=200, seed=1, max_solutions=10):
    """Apply local search to (up to max_solutions) front members; return non-dominated union."""
    out = list(front)
    chosen = front if len(front) <= max_solutions else [front[i] for i in np.linspace(0, len(front) - 1, max_solutions).astype(int)]
    for k, (g, _) in enumerate(chosen):
        ng, no, _ = hill_climb(prob, g, iterations, seed + k)
        out.append((ng, no))
    return pareto_filter(out)

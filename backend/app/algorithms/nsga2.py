"""NSGA-II via pymoo with timetable-aware sampling / crossover / mutation.
Objectives are NOT scalarised: pymoo performs non-dominated sorting + crowding distance.
Hard constraints are handled through pymoo's constraint domination (G = number of hard violations <= 0)."""
import random, time
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem as PymooProblem
from pymoo.core.sampling import Sampling
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.core.callback import Callback
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from app.algorithms.problem import OBJ_NAMES


class _TTProblem(PymooProblem):
    def __init__(self, prob):
        n = len(prob.sessions) * 3
        super().__init__(n_var=n, n_obj=len(OBJ_NAMES), n_ieq_constr=1, xl=0, xu=max(prob.rooms.__len__(), prob.periods, prob.days) + 1)
        self.tt = prob
    def _evaluate(self, X, out, *a, **k):
        F, G = [], []
        for row in X:
            h, o = self.tt.evaluate(np.rint(row).astype(int).reshape(-1, 3))
            F.append(o); G.append([h])
        out["F"] = np.array(F); out["G"] = np.array(G, dtype=float)


class _Sampling(Sampling):
    def __init__(self, prob, seed): super().__init__(); self.tt, self.rng = prob, random.Random(seed)
    def _do(self, problem, n_samples, **kw):
        return np.array([self.tt.random_solution(self.rng).flatten() for _ in range(n_samples)], dtype=int)

class _Crossover(Crossover):
    def __init__(self, prob, seed): super().__init__(2, 2); self.tt, self.rng = prob, random.Random(seed + 1)
    def _do(self, problem, X, **kw):
        _, n_m, n_v = X.shape; Y = np.empty_like(X)
        for k in range(n_m):
            c1, c2 = self.tt.crossover(X[0, k].astype(int), X[1, k].astype(int), self.rng)
            Y[0, k], Y[1, k] = c1.flatten(), c2.flatten()
        return Y

class _Mutation(Mutation):
    def __init__(self, prob, seed, rate=0.4):
        super().__init__(); self.tt, self.rng, self.rate = prob, random.Random(seed + 2), rate
    def _do(self, problem, X, **kw):
        Y = X.copy().astype(int)
        for k in range(len(X)):
            if self.rng.random() < self.rate:
                Y[k] = self.tt.mutate(Y[k], self.rng, n_moves=self.rng.randint(1, 3)).flatten()
        return Y

class _CB(Callback):
    def __init__(self, fn): super().__init__(); self.fn, self.t = fn, time.perf_counter()
    def notify(self, algorithm):
        now = time.perf_counter(); G = algorithm.pop.get("G")[:, 0]; opt = algorithm.opt
        rec = {"generation": int(algorithm.n_gen), "candidates": len(algorithm.pop),
               "best_hard": int(G.min()), "feasible": int((G <= 0).sum()), "pareto_size": int(len(opt)),
               "best_objectives": [float(v) for v in opt.get("F")[np.argmin(opt.get("F").sum(axis=1))]] if len(opt) else [],
               "duration_s": round(now - self.t, 4)}
        self.t = now
        if self.fn: self.fn(rec)


def run_nsga2(prob, pop_size=40, generations=50, seed=1, callback=None):
    history = []
    def cb(rec): history.append(rec); callback and callback(rec)
    algo = NSGA2(pop_size=pop_size, sampling=_Sampling(prob, seed), crossover=_Crossover(prob, seed),
                 mutation=_Mutation(prob, seed), eliminate_duplicates=True)
    res = minimize(_TTProblem(prob), algo, get_termination("n_gen", generations), seed=seed, verbose=False,
                   callback=_CB(cb))
    pop = res.pop; G = pop.get("G")[:, 0]; X = pop.get("X"); F = pop.get("F")
    feas = [(np.rint(X[i]).astype(int).reshape(-1, 3), F[i]) for i in range(len(pop)) if G[i] <= 0]
    front = pareto_filter(feas)
    best_inf = None
    if not front:
        i = int(np.argmin(G)); best_inf = (np.rint(X[i]).astype(int).reshape(-1, 3), int(G[i]), F[i])
    return {"front": front, "history": history, "best_infeasible": best_inf}


def dominates(a, b):
    return bool(np.all(a <= b) and np.any(a < b))

def pareto_filter(items):
    """items: [(genes, objs)] -> non-dominated, de-duplicated by genes."""
    uniq = {}
    for g, o in items: uniq[tuple(np.asarray(g).flatten())] = (np.asarray(g), np.asarray(o, dtype=float))
    lst = list(uniq.values())
    return [(g, o) for i, (g, o) in enumerate(lst) if not any(dominates(o2, o) for j, (_, o2) in enumerate(lst) if j != i)]

"""Baseline single-objective Genetic Algorithm (weighted-sum fitness, elitist replacement)."""
import random, time
import numpy as np

def run_ga(prob, pop_size=40, generations=60, crossover_rate=0.9, mutation_rate=0.3, elite=2, seed=1, callback=None):
    rng = random.Random(seed)
    pop = [prob.random_solution(rng) for _ in range(pop_size)]
    def fit(g):
        h, o = prob.evaluate(g); return prob.scalar(h, o), h, o
    scored = [(fit(g), g) for g in pop]
    history = []
    for gen in range(1, generations + 1):
        t0 = time.perf_counter()
        scored.sort(key=lambda x: x[0][0])
        nxt = [(f, g.copy()) for f, g in scored[:elite]]                      # elitism
        def tour():                                                          # tournament selection (k=3)
            return min(rng.sample(scored, 3), key=lambda x: x[0][0])[1]
        while len(nxt) < pop_size:
            a, b = tour(), tour()
            c1, c2 = prob.crossover(a, b, rng) if rng.random() < crossover_rate else (a.copy(), b.copy())
            for c in (c1, c2):
                if rng.random() < mutation_rate: c = prob.mutate(c, rng, n_moves=rng.randint(1, 3))
                nxt.append((fit(c), c))
        scored = nxt[:pop_size]                                              # generational replacement
        best = min(scored, key=lambda x: x[0][0])
        rec = {"generation": gen, "candidates": len(scored), "best_hard": int(best[0][1]),
               "best_objectives": [float(v) for v in best[0][2]], "best_fitness": float(best[0][0]),
               "duration_s": round(time.perf_counter() - t0, 4)}
        history.append(rec)
        if callback: callback(rec)
    scored.sort(key=lambda x: x[0][0])
    (fv, h, o), g = scored[0]
    return {"best": (g, int(h), o), "history": history}

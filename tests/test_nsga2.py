import numpy as np
from app.algorithms.nsga2 import run_nsga2, dominates

def test_nsga2_feasible_pareto_front(prob):
    r = run_nsga2(prob, pop_size=20, generations=8, seed=1)
    front = r["front"]; assert front
    for g, o in front: assert prob.hard_count(g) == 0 and np.allclose(prob.objectives(g), o)
    for i, (_, a) in enumerate(front):               # mutually non-dominated
        for j, (_, b) in enumerate(front):
            if i != j: assert not dominates(a, b)
    assert len(r["history"]) == 8 and r["history"][-1]["pareto_size"] >= 1

def test_nsga2_uses_multiple_objectives_not_weighted_sum(prob):
    front = run_nsga2(prob, pop_size=20, generations=8, seed=2)["front"]
    assert len({tuple(np.round(o, 3)) for _, o in front}) > 1   # several distinct trade-off solutions

def test_nsga2_operators_preserve_validity(prob, feasible):
    import random; rng = random.Random(0)
    for _ in range(20):
        assert prob.hard_count(prob.mutate(feasible, rng, 3)) == 0   # mutation only makes feasible moves
    c1, c2 = prob.crossover(feasible, prob.random_solution(rng), rng)
    assert prob.hard_count(c1) == 0 and prob.hard_count(c2) == 0

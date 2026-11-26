import random, numpy as np, pytest
from app.algorithms.local_search import hill_climb, improve_front
from app.algorithms.nsga2 import dominates

def test_local_search_never_worse_and_stays_feasible(prob):
    g0 = prob.random_solution(random.Random(11)); h, o0 = prob.evaluate(g0); assert h == 0
    g1, o1, n = hill_climb(prob, g0, iterations=300, seed=1)
    assert prob.hard_count(g1) == 0 and np.all(o1 <= o0)
    assert np.any(o1 < o0) and n > 0     # random start has plenty of room to improve

def test_local_search_rejects_infeasible_input(prob, feasible):
    g = feasible.copy(); g[0][:2] = g[1][:2]; g[2][:2] = g[1][:2]
    if prob.hard_count(g) == 0: pytest.skip("perturbation happened to stay feasible")
    with pytest.raises(ValueError): hill_climb(prob, g)

def test_improve_front_returns_nondominated_feasible(prob):
    starts = [(prob.random_solution(random.Random(s)), None) for s in (1, 2, 3)]
    front = [(g, prob.objectives(g)) for g, _ in starts]
    out = improve_front(prob, front, iterations=100, seed=1)
    for i, (g, o) in enumerate(out):
        assert prob.hard_count(g) == 0
        assert not any(dominates(o2, o) for j, (_, o2) in enumerate(out) if j != i)

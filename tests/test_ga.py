import numpy as np
from app.algorithms.ga import run_ga

def test_ga_returns_feasible_and_improves(prob):
    r = run_ga(prob, pop_size=16, generations=10, seed=2)
    g, h, o = r["best"]; assert h == 0 and prob.hard_count(g) == 0
    assert len(r["history"]) == 10 and r["history"][-1]["best_fitness"] <= r["history"][0]["best_fitness"]

def test_ga_every_session_scheduled(prob):
    g = run_ga(prob, 10, 3, seed=1)["best"][0]
    assert g.shape == (len(prob.sessions), 3)
    for key, idxs in prob.by_key.items():   # weekly hours per (section, subject) are fully scheduled
        assert sum(prob.sessions[i].duration for i in idxs) == prob.subjects[key[1]]["hours"]

def test_ga_reproducible(prob):
    a = run_ga(prob, 10, 3, seed=4)["best"]; b = run_ga(prob, 10, 3, seed=4)["best"]
    assert np.array_equal(a[0], b[0])

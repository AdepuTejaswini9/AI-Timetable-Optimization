"""Incremental re-optimisation: repair only the assignments hit by an unavailability event."""
import copy, random
import numpy as np
from app.algorithms.explain import describe, _n, _slot

def apply_event(prob, event):
    """event: {type: 'faculty'|'room', id: <faculty_id|room_id>, slots: [[day, period],...] | None (=whole week)}"""
    p = copy.deepcopy(prob)
    slots = None if not event.get("slots") else {tuple(s) for s in event["slots"]}
    if event["type"] == "faculty":
        fa = p.faculty[event["id"]]
        fa["unavailable"] |= slots if slots is not None else {(d, q) for d in range(p.days) for q in range(p.periods)}
    elif event["type"] == "room":
        ri = next(i for i, r in enumerate(p.rooms) if r["id"] == event["id"])
        if slots is None: p.rooms[ri]["available"] = False
        else: p.rooms[ri]["unavailable"] |= slots
    else:
        raise ValueError("unknown event type")
    p.refresh()
    return p

def _try_repair(p, genes, free_set, rng, attempts):
    """Randomised greedy re-placement of the unlocked sessions; everything else stays locked."""
    base = Occ_without(p, genes, free_set)
    best = None
    for _ in range(attempts):
        occ = copy_occ(base); g = genes.copy(); ok = True
        order = sorted(free_set, key=lambda i: len(p.cand_slots[i]) * len(p.cand_rooms[i]) * (0.5 + rng.random()))
        for i in order:
            pos = _best_position(p, occ, g, i, rng)
            if pos is None: ok = False; break
            g[i] = pos; occ.place(i, *pos)
        if ok:
            h, o = p.evaluate(g)
            if h == 0 and (best is None or p.scalar(h, o) < best[0]): best = (p.scalar(h, o), g)
            if attempts > 1 and best: break
    return best[1] if best else None

def Occ_without(p, genes, free_set):
    from app.algorithms.problem import Occ
    occ = Occ(p)
    for i in range(len(p.sessions)):
        if i not in free_set: occ.place(i, *map(int, genes[i]))
    return occ

def copy_occ(o):
    import copy as c
    n = c.copy(o); n.fac, n.sec, n.room, n.fday = dict(o.fac), dict(o.sec), dict(o.room), dict(o.fday); return n

def _best_position(p, occ, genes, i, rng, samples=40):
    """Pick the feasible position with the lowest soft cost among a random sample (keeps repairs high quality)."""
    cands = []
    slots = p.cand_slots[i][:]; rng.shuffle(slots)
    for d, q in slots:
        for r in p.cand_rooms[i]:
            if occ.free(i, d, q, r): cands.append((d, q, r))
        if len(cands) >= samples: break
    if not cands: return None
    best, bs = None, None
    for c in cands:
        t = genes.copy(); t[i] = c
        sc = float(np.dot([1] * 5, p.objectives(t)))  # other sessions fixed -> comparable local cost
        if bs is None or sc < bs: best, bs = c, sc
    return best

def reoptimize(prob, genes, event, seed=1, max_levels=3, attempts=60):
    """Returns dict(success, genes, affected, unlocked, level, changed, violations, reason, suggestions)."""
    rng = random.Random(seed)
    genes = np.array(genes, dtype=int).reshape(-1, 3)
    p = apply_event(prob, event)
    affected = sorted({i for v in p.analyze(genes) for i in v[1]})
    res = {"affected": affected, "affected_details": [], "success": False}
    for i in affected:
        s = p.sessions[i]
        res["affected_details"].append({"session": i, "section": _n(p, "section", s.section_id),
            "subject": _n(p, "subject", s.subject_id), "faculty": _n(p, "faculty", s.faculty_id),
            "room": p.rooms[int(genes[i][2])]["name"], "slot": _slot(int(genes[i][0]), int(genes[i][1]))})
    if not affected:
        return {**res, "success": True, "genes": genes, "unlocked": [], "level": 0, "changed": [], "violations": [],
                "reason": "No timetable entry is affected by this event."}
    free = set(affected)
    for level in range(0, max_levels + 1):
        if level > 0:  # expand repair set with dependent sessions
            add = set()
            for i in affected:
                s = p.sessions[i]
                for j, t in enumerate(p.sessions):
                    if j in free: continue
                    if level == 1 and t.section_id == s.section_id: add.add(j)
                    elif level == 2 and (t.faculty_id == s.faculty_id or t.section_id == s.section_id): add.add(j)
                    elif level == 3: add.add(j)
            if not add - free: continue
            free |= add
        sol = _try_repair(p, genes, free, rng, attempts)
        if sol is not None:
            changed = [int(i) for i in range(len(genes)) if tuple(sol[i]) != tuple(genes[i])]
            viol = p.analyze(sol)
            if viol: continue
            return {**res, "success": True, "genes": sol, "unlocked": sorted(free), "level": level,
                    "changed": changed, "violations": [],
                    "reason": f"Repaired by re-placing {len(changed)} of {len(genes)} entries (expansion level {level})."}
    # failure: keep original, explain
    reasons, sugg = [], []
    for i in affected:
        s = p.sessions[i]; n_slots = len(p.cand_slots[i]); n_rooms = len(p.cand_rooms[i])
        if n_slots == 0 or n_rooms == 0:
            reasons.append(f"{_n(p,'subject',s.subject_id)} / {_n(p,'section',s.section_id)}: no "
                           f"{'slot for ' + _n(p,'faculty',s.faculty_id) if n_slots == 0 else 'suitable room'} remains (proven).")
        else:
            reasons.append(f"{_n(p,'subject',s.subject_id)} / {_n(p,'section',s.section_id)}: no conflict-free placement "
                           f"found within the search limit ({attempts} randomised attempts per expansion level) – "
                           "this is NOT a proof of infeasibility.")
        fa = [(fid, f) for fid, f in p.faculty.items() if fid != s.faculty_id and f["department_id"] == p.faculty[s.faculty_id]["department_id"]]
        if fa: sugg.append(f"Assign a substitute for {_n(p,'subject',s.subject_id)} from: " + ", ".join(_n(p, 'faculty', fid) for fid, _ in fa[:4]))
    sugg += ["Relax the unavailability window, add a room, or increase the search limit and retry."]
    return {**res, "success": False, "genes": genes, "unlocked": sorted(free), "level": max_levels, "changed": [],
            "violations": describe(p, genes), "reason": " ".join(reasons), "suggestions": sugg}

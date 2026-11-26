import copy, numpy as np
from app.algorithms.problem import Problem
from app.algorithms.explain import describe, proof_of_infeasibility
from app.services.data_loader import entries_to_genes
from app.models import TimetableEntry

def types(prob, g): return {v[0] for v in prob.analyze(g)}
def same_fac(prob, key=None):
    """two sessions of the same faculty (different sections or subjects)"""
    for f in prob.faculty:
        idx = [s.idx for s in prob.sessions if s.faculty_id == f and not s.is_lab]
        if len(idx) >= 2: return idx[0], idx[1]

def test_feasible_baseline(prob, feasible): assert prob.hard_count(feasible) == 0

def test_faculty_clash(prob, feasible):
    a, b = same_fac(prob); g = feasible.copy(); g[b][:2] = g[a][:2]
    assert "FACULTY_CLASH" in types(prob, g)

def test_room_clash(prob, feasible):
    a = 0; b = next(s.idx for s in prob.sessions if s.idx != a and not s.is_lab and not prob.sessions[a].is_lab)
    g = feasible.copy(); g[b] = g[a]
    assert "ROOM_CLASH" in types(prob, g)

def test_section_clash(prob, feasible):
    sec = prob.sessions[0].section_id
    a, b = [s.idx for s in prob.sessions if s.section_id == sec][:2]
    g = feasible.copy(); g[b][:2] = g[a][:2]
    assert "SECTION_CLASH" in types(prob, g)

def test_room_capacity(prob, feasible):
    i = next(s.idx for s in prob.sessions if not s.is_lab and s.size == 55)
    small = next(k for k, r in enumerate(prob.rooms) if not r["is_lab"] and r["capacity"] < 55)
    g = feasible.copy(); g[i][2] = small
    assert "ROOM_CAPACITY" in types(prob, g)

def test_lab_room_type(prob, feasible):
    i = next(s.idx for s in prob.sessions if s.is_lab); g = feasible.copy()
    g[i][2] = next(k for k, r in enumerate(prob.rooms) if not r["is_lab"])
    assert "ROOM_TYPE" in types(prob, g)

def test_lab_duration_cannot_cross_break(prob, feasible):
    i = next(s.idx for s in prob.sessions if s.is_lab); g = feasible.copy(); g[i][1] = prob.break_after  # block spans lunch
    assert "INVALID_SLOT" in types(prob, g)
    j = i; g = feasible.copy(); g[j][1] = prob.periods - 1  # block runs past end of day
    assert "INVALID_SLOT" in types(prob, g)

def test_faculty_availability(prob, feasible):
    f = next(fid for fid, v in prob.faculty.items() if v["unavailable"])
    i = next(s.idx for s in prob.sessions if s.faculty_id == f and not s.is_lab)
    d, p = sorted(prob.faculty[f]["unavailable"])[0]; g = feasible.copy(); g[i][:2] = (d, p)
    assert "FACULTY_UNAVAILABLE" in types(prob, g)

def test_daily_load_limit(prob, feasible):
    q = copy.deepcopy(prob); f = prob.sessions[0].faculty_id; q.faculty[f]["max_daily"] = 1
    assert "FACULTY_DAILY_LOAD" in types(q, feasible)

def test_required_weekly_hours_verified_on_db_entries(prob, db, published):
    ents = db.query(TimetableEntry).filter_by(version_id=published).all()
    genes, extra = entries_to_genes(prob, ents); assert extra == [] and prob.hard_count(genes) == 0
    genes, extra = entries_to_genes(prob, ents[1:])      # drop one session
    assert any(x["type"] == "REQUIRED_HOURS" for x in extra)

def test_explanations_are_structured(prob, feasible):
    a, b = same_fac(prob); g = feasible.copy(); g[b][:2] = g[a][:2]
    rep = [r for r in describe(prob, g) if r["type"] == "FACULTY_CLASH"][0]
    for k in ("faculty", "subject", "section", "room", "slot", "explanation", "suggestion"): assert rep[k] is not None

def test_proven_infeasibility_detected(prob):
    q = copy.deepcopy(prob)
    for r in q.rooms: r["capacity"] = 10
    q.refresh(); assert any(r["type"] == "NO_SUITABLE_ROOM" for r in proof_of_infeasibility(q))
    q2 = copy.deepcopy(prob); f = prob.sessions[0].faculty_id; q2.faculty[f]["max_weekly"] = 1
    assert any(r["type"] == "REQUIRED_HOURS_EXCEED_CAPACITY" for r in proof_of_infeasibility(q2))
    assert proof_of_infeasibility(prob) == []

def test_manual_edit_is_validated(client, headers, published):
    h = headers["admin"]
    vid = client.post(f"/timetable/{published}/clone", headers=h).json()["version_id"]
    ents = client.get(f"/timetable/{vid}", headers=h).json()["entries"]
    a = ents[0]; b = next(e for e in ents if e["faculty_id"] == a["faculty_id"] and e["id"] != a["id"] and not e["is_lab"] and not a["is_lab"])
    r = client.put(f"/timetable/{vid}", headers=h, json={"entry_id": b["id"], "day": a["day"], "period": a["period"], "room_id": b["room_id"]})
    assert r.status_code == 422 and any(v["type"] == "FACULTY_CLASH" for v in r.json()["detail"]["violations"])
    after = client.get(f"/timetable/{vid}", headers=h).json()["entries"]
    assert next(e for e in after if e["id"] == b["id"])["day"] == b["day"]   # rejected change not saved
    assert client.put(f"/timetable/{published}", headers=h, json={"entry_id": a["id"], "day": 0, "period": 0, "room_id": 1}).status_code == 409

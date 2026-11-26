import numpy as np
from app.algorithms.reoptimize import reoptimize

def test_incremental_repair_preserves_unaffected_entries(prob, feasible):
    s = prob.sessions[0]; d, p = int(feasible[0][0]), int(feasible[0][1])
    res = reoptimize(prob, feasible, {"type": "faculty", "id": s.faculty_id, "slots": [[d, p]]}, seed=1)
    assert res["success"] and 0 in res["affected"]
    g = res["genes"]; assert prob.hard_count(g) == 0
    assert tuple(g[0][:2]) != (d, p)                                    # moved away from unavailable slot
    for i in range(len(g)):                                              # entries outside repair set are untouched
        if i not in res["unlocked"]: assert tuple(g[i]) == tuple(feasible[i])
    assert len(res["changed"]) < len(g) / 2                              # not a full regeneration

def test_room_unavailable_repair(prob, feasible):
    ri = int(feasible[0][2]); rid = prob.rooms[ri]["id"]
    res = reoptimize(prob, feasible, {"type": "room", "id": rid, "slots": None}, seed=1)
    assert res["success"] and all(int(r) != ri for r in res["genes"][:, 2]) and prob.hard_count(res["genes"]) == 0

def test_unaffected_event_changes_nothing(prob, feasible):
    f = prob.sessions[0].faculty_id; busy = {(int(feasible[i][0]), int(feasible[i][1])) for i, s in enumerate(prob.sessions) if s.faculty_id == f}
    free = next((d, p) for d in range(prob.days) for p in range(prob.periods) if (d, p) not in busy)
    res = reoptimize(prob, feasible, {"type": "faculty", "id": f, "slots": [list(free)]})
    assert res["success"] and res["changed"] == [] and np.array_equal(res["genes"], feasible)

def test_failed_repair_keeps_original_and_explains(prob, feasible):
    f = prob.sessions[0].faculty_id     # whole-week unavailability of the only teacher of the subject -> impossible
    res = reoptimize(prob, feasible, {"type": "faculty", "id": f, "slots": None})
    assert not res["success"] and np.array_equal(res["genes"], feasible)
    assert "proven" in res["reason"].lower() and res["suggestions"] and res["affected_details"]

def test_api_new_version_and_original_preserved(client, headers, published):
    h = headers["admin"]
    before = client.get(f"/timetable/{published}", headers=h).json()["entries"]
    e = before[0]
    r = client.post("/reoptimization/request", headers=h, json={"version_id": published, "event_type": "faculty",
                    "faculty_id": e["faculty_id"], "slots": [{"day": e["day"], "period": e["period"]}]})
    assert r.status_code == 201, r.text; out = r.json()
    assert out["success"] and out["new_version_id"] and out["new_version_id"] != published
    nv = client.get(f"/timetable/{out['new_version_id']}", headers=h).json()
    assert nv["version"]["parent_version_id"] == published and nv["version"]["hard_violations"] == 0
    assert nv["version"]["status"] == "draft"
    after = client.get(f"/timetable/{published}", headers=h).json()
    assert after["version"]["status"] == "published" and after["entries"] == before     # original untouched
    st = client.get(f"/reoptimization/{out['run_id']}/status", headers=h).json(); assert st["outcome"] == "repaired"
    assert client.get(f"/timetable/{out['new_version_id']}/conflicts", headers=h).json()["hard_violation_count"] == 0

def test_api_failed_repair_preserves_published(client, headers, published):
    h = headers["admin"]; before = client.get(f"/timetable/{published}", headers=h).json()["entries"]
    r = client.post("/reoptimization/request", headers=h, json={"version_id": published, "event_type": "faculty", "faculty_id": before[0]["faculty_id"]})
    out = r.json(); assert r.status_code == 201 and out["success"] is False and out["new_version_id"] is None
    assert out["affected"] and out["suggestions"] and out["violations"]
    assert client.get(f"/timetable/{published}", headers=h).json()["entries"] == before

def test_hod_request_goes_to_admin(client, headers, published):
    fid = client.get("/faculty", headers=headers["hod_cse"]).json()[0]["id"]
    r = client.post("/reoptimization/request", headers=headers["hod_cse"], json={"version_id": published, "event_type": "faculty", "faculty_id": fid})
    assert r.status_code == 201 and r.json()["status"] == "pending_admin"
    other = client.get("/faculty", headers=headers["hod_ece"]).json()[0]["id"]
    assert client.post("/reoptimization/request", headers=headers["hod_cse"], json={"version_id": published, "event_type": "faculty", "faculty_id": other}).status_code == 403

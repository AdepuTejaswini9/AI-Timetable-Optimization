def test_unauthenticated_blocked(client):
    for path in ["/faculty", "/subjects", "/timetable", "/dashboard", "/optimization"]:
        assert client.get(path).status_code == 401

def test_role_restrictions(client, headers):
    assert client.get("/faculty", headers=headers["student"]).status_code == 403
    assert client.post("/subjects", headers=headers["faculty"], json={"code": "X", "name": "X", "department_id": 1, "semester": 1, "weekly_hours": 2}).status_code == 403
    assert client.post("/optimization/generate", headers=headers["hod_cse"], json={}).status_code == 403
    assert client.post("/timetable/generate", headers=headers["faculty"], json={}).status_code == 403

def test_hod_department_isolation(client, headers):
    cse = client.get("/faculty", headers=headers["hod_cse"]).json()
    assert len(cse) == 5 and all(f["department_id"] == cse[0]["department_id"] for f in cse)
    ece_id = client.get("/faculty", headers=headers["hod_ece"]).json()[0]["id"]
    assert client.get(f"/faculty/{ece_id}", headers=headers["hod_cse"]).status_code == 403
    assert client.get("/departments", headers=headers["hod_cse"]).json().__len__() == 1
    secs = client.get("/sections", headers=headers["hod_cse"]).json()
    assert {s["department_id"] for s in secs} == {cse[0]["department_id"]}

def test_hod_cannot_decide_other_department(client, headers, published):
    # published workflow already approved; create a fresh draft & submit to test cross-department approval
    h = headers["admin"]
    vid = client.post("/timetable/generate", json={"algorithm": "ga", "population": 10, "generations": 3, "seed": 5}, headers=h).json()["version_id"]
    client.post("/approvals/submit", json={"version_id": vid}, headers=h)
    recs = [a for a in client.get("/approvals", headers=h).json() if a["version_id"] == vid]
    cse_dept = client.get("/hods", headers=h).json()[0]["department_id"]
    other = next(a for a in recs if a["department_id"] != cse_dept)
    assert client.post(f"/approvals/{other['id']}/approve", json={}, headers=headers["hod_cse"]).status_code == 403
    assert client.post(f"/approvals/{other['id']}/reject", json={"comment": "no"}, headers=headers["hod_cse"]).status_code == 403

def test_student_sees_only_own_section(client, headers, published):
    me = client.get("/auth/me", headers=headers["student"]).json()
    r = client.get(f"/timetable/{published}", headers=headers["student"]); assert r.status_code == 200
    assert r.json()["entries"] and {e["section_id"] for e in r.json()["entries"]} == {me["section_id"]}
    other = client.get(f"/timetable/{published}?section_id={me['section_id'] + 1}", headers=headers["student"]).json()
    assert other["entries"] == []   # filter cannot widen scope
    assert client.get("/sections", headers=headers["student"]).status_code == 403

def test_faculty_sees_only_own_classes(client, headers, published):
    fid = client.get("/auth/me", headers=headers["faculty"]).json()["faculty_id"]
    ents = client.get(f"/timetable/{published}", headers=headers["faculty"]).json()["entries"]
    assert ents and {e["faculty_id"] for e in ents} == {fid}

def test_hod_sees_only_department(client, headers, published):
    dept = client.get("/auth/me", headers=headers["hod_ece"]).json()["department_id"]
    ents = client.get(f"/timetable/{published}", headers=headers["hod_ece"]).json()["entries"]
    assert ents and {e["department_id"] for e in ents} == {dept}

def test_drafts_hidden_from_students(client, headers, published):
    admin_list = client.get("/timetable", headers=headers["admin"]).json()
    draft = next(v for v in admin_list if v["status"] in ("draft", "pending"))
    assert client.get(f"/timetable/{draft['id']}", headers=headers["student"]).status_code == 404
    assert all(v["status"] == "published" for v in client.get("/timetable", headers=headers["student"]).json())

def test_faculty_cannot_edit_timetable_or_publish(client, headers, published):
    assert client.put(f"/timetable/{published}", headers=headers["faculty"], json={"entry_id": 1, "day": 0, "period": 0, "room_id": 1}).status_code == 403
    assert client.post(f"/timetable/{published}/publish", headers=headers["hod_cse"]).status_code == 403

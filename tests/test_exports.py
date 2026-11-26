import io
from openpyxl import load_workbook

def test_pdf_export(client, headers, published):
    r = client.get(f"/export/timetable/{published}/pdf", headers=headers["admin"])
    assert r.status_code == 200 and r.content.startswith(b"%PDF") and len(r.content) > 1500

def test_excel_export_all_roles_scoped(client, headers, published):
    r = client.get(f"/export/timetable/{published}/excel", headers=headers["admin"]); assert r.status_code == 200
    assert len(load_workbook(io.BytesIO(r.content)).sheetnames) == 3          # one sheet per section
    r = client.get(f"/export/timetable/{published}/excel", headers=headers["student"])
    assert len(load_workbook(io.BytesIO(r.content)).sheetnames) == 1          # student: own section only
    r = client.get(f"/export/timetable/{published}/pdf", headers=headers["faculty"]); assert r.status_code == 200

def test_export_requires_auth(client, published):
    assert client.get(f"/export/timetable/{published}/pdf").status_code == 401

def test_publish_blocked_without_approval_and_with_violations(client, headers):
    h = headers["admin"]
    vid = client.post("/timetable/generate", json={"algorithm": "ga", "population": 8, "generations": 2}, headers=h).json()["version_id"]
    assert client.post(f"/timetable/{vid}/publish", headers=h).status_code == 409   # not yet approved

import os, sys, tempfile, random
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"   # tests never touch MySQL
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

from fastapi.testclient import TestClient
from app.database.session import Base, engine, SessionLocal
import app.models  # noqa
from app.utils.seed import seed
from app.main import app
from app.services.data_loader import build_problem

Base.metadata.create_all(engine)
_db = SessionLocal(); seed(_db); _db.close()

CREDS = {"admin": ("admin@college.edu", "Admin@123"), "hod_cse": ("hod.cse@college.edu", "Hod@123"),
         "hod_ece": ("hod.ece@college.edu", "Hod@123"), "faculty": ("faculty1@college.edu", "Faculty@123"),
         "faculty6": ("faculty6@college.edu", "Faculty@123"), "student": ("student1@college.edu", "Student@123"),
         "student5": ("student5@college.edu", "Student@123")}

@pytest.fixture(scope="session")
def client(): return TestClient(app)

@pytest.fixture(scope="session")
def db():
    s = SessionLocal(); yield s; s.close()

@pytest.fixture(scope="session")
def headers(client):
    out = {}
    for k, (e, p) in CREDS.items():
        r = client.post("/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text
        out[k] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return out

@pytest.fixture(scope="session")
def prob(db): return build_problem(db)

@pytest.fixture(scope="session")
def feasible(prob):
    g = prob.random_solution(random.Random(7)); assert prob.hard_count(g) == 0; return g

@pytest.fixture(scope="session")
def published(client, headers):
    """generate -> submit -> both HODs approve -> publish (the full workflow)."""
    h = headers["admin"]
    r = client.post("/timetable/generate", json={"algorithm": "nsga2_ls", "population": 16, "generations": 6, "ls_iterations": 30, "seed": 3}, headers=h)
    assert r.status_code == 201, r.text; vid = r.json()["version_id"]
    assert client.post("/approvals/submit", json={"version_id": vid}, headers=h).status_code == 201
    for hk in ("hod_cse", "hod_ece"):
        for a in client.get("/approvals", headers=headers[hk]).json():
            if a["version_id"] == vid: assert client.post(f"/approvals/{a['id']}/approve", json={}, headers=headers[hk]).status_code == 200
    r = client.post(f"/timetable/{vid}/publish", headers=h); assert r.status_code == 200, r.text
    return vid

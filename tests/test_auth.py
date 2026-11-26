import pytest
from conftest import CREDS

@pytest.mark.parametrize("role", ["admin", "hod_cse", "faculty", "student"])
def test_login_all_roles(client, role):
    e, p = CREDS[role]
    r = client.post("/auth/login", json={"email": e, "password": p})
    assert r.status_code == 200 and r.json()["user"]["role"] == role.split("_")[0]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == e

def test_wrong_password_and_unknown_user(client):
    assert client.post("/auth/login", json={"email": "admin@college.edu", "password": "nope"}).status_code == 401
    assert client.post("/auth/login", json={"email": "x@y.z", "password": "nope"}).status_code == 401

def test_no_or_bad_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401

def test_passwords_hashed(db):
    from app.models import User
    for u in db.query(User): assert u.password_hash.startswith("$2") and "@123" not in u.password_hash

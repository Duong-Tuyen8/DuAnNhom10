from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_admin_token():
    r = client.post("/auth/login", json={"username": "chunhiem", "password": "123456"})
    return r.json()["access_token"]


def admin_headers():
    return {"Authorization": f"Bearer {get_admin_token()}"}


def test_create_member():
    r = client.post("/members", headers=admin_headers(), json={
        "full_name": "Trần Thị B",
        "student_id": "SV010",
        "email": "b@test.edu.vn",
        "phone": "0900000002",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["full_name"] == "Trần Thị B"
    assert data["student_id"] == "SV010"


def test_delete_member():
    # Create, then delete (soft)
    r = client.post("/members", headers=admin_headers(), json={"full_name": "Temp", "student_id": "SVX", "email": "temp@test.vn"})
    mid = r.json()["id"]

    d = client.delete(f"/members/{mid}", headers=admin_headers())
    assert d.status_code == 204

    g = client.get(f"/members/{mid}", headers=admin_headers())
    assert g.status_code == 200
    assert g.json()["is_active"] == False


def test_member_search():
    lst = client.get("/members", params={"search": "B"}, headers=admin_headers())
    assert lst.status_code == 200
    names = [m["full_name"] for m in lst.json()]
    assert any("B" in n for n in names)
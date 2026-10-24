from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_admin_token():
    r = client.post("/auth/login", json={"username": "chunhiem", "password": "123456"})
    return r.json()["access_token"]


def admin_headers():
    return {"Authorization": f"Bearer {get_admin_token()}"}


def test_overview_stats():
    r = client.get("/stats/overview", headers=admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert "total_members" in data
    assert "total_committees" in data
    assert data["total_members"] >= 1


def test_activity_stats():
    r = client.get("/stats/activities", headers=admin_headers())
    assert r.status_code == 200
    # Should not raise even with empty data


def test_top_members():
    r = client.get("/stats/members/top", params={"limit": 5}, headers=admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_member_participation():
    members = client.get("/members", headers=admin_headers()).json()
    if members:
        mid = members[0]["id"]
        r = client.get("/stats/members/participation", params={"member_id": mid}, headers=admin_headers())
        assert r.status_code == 200
        assert "activities" in r.json()
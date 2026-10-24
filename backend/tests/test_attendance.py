from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

client = TestClient(app)


def get_user_token(username, password):
    r = client.post("/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


def auth_admin():
    return {"Authorization": f"Bearer {get_user_token('chunhiem', '123456')}"}


def test_attendance_flow():
    # Create activity
    now = datetime.utcnow()
    act = client.post("/activities", headers=auth_admin(), json={
        "title": "Meeting Test",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
    }).json()

    # List members to find a valid id
    members = client.get("/members", headers=auth_admin()).json()
    member_id = members[0]["id"]

    # Create attendance
    r = client.post("/attendance", headers=auth_admin(), json={
        "activity_id": act["id"],
        "member_id": member_id,
        "status": "present",
        "feedback": "Hay tham gi",
    })
    assert r.status_code == 201
    att = r.json()
    assert att["status"] == "present"

    # Duplicate should be rejected
    dup = client.post("/attendance", headers=auth_admin(), json={
        "activity_id": act["id"], "member_id": member_id, "status": "present",
    })
    assert dup.status_code == 400

    # Update attendance status
    upd = client.put(f"/attendance/{att['id']}", params={"status": "late"}, headers=auth_admin())
    assert upd.status_code == 200
    assert upd.json()["status"] == "late"

    # List by activity
    lst = client.get("/attendance", params={"activity_id": act["id"]}, headers=auth_admin())
    assert lst.status_code == 200
    assert len(lst.json()) == 1
    assert lst.json()[0]["member_name"]
    assert lst.json()[0]["student_id"] == members[0]["student_id"]


def test_attendance_invalid_status():
    members = client.get("/members", headers=auth_admin()).json()
    now = datetime.utcnow()
    act = client.post("/activities", headers=auth_admin(), json={
        "title": "A2", "start_time": now.isoformat(), "end_time": (now + timedelta(hours=1)).isoformat(),
    }).json()
    r = client.post("/attendance", headers=auth_admin(), json={
        "activity_id": act["id"], "member_id": members[0]["id"], "status": "maybe",
    })
    assert r.status_code == 400
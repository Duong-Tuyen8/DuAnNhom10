from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.models import Activity

client = TestClient(app)


def get_token():
    r = client.post("/auth/login", json={"username": "chunhiem", "password": "123456"})
    return r.json()["access_token"]


def auth():
    return {"Authorization": f"Bearer {get_token()}"}


def _create_activity():
    """Helper: create one activity and return its id."""
    now = datetime.utcnow()
    r = client.post("/activities", headers=auth(), json={
        "title": "Workshop IT",
        "description": "Tech workshop",
        "location": "Hội trường B",
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=3)).isoformat(),
    })
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["title"] == "Workshop IT"
    assert data["attendee_count"] == 0
    return data["id"]


def test_create_activity():
    _create_activity()


def test_create_activity_invalid_time():
    now = datetime.utcnow()
    r = client.post("/activities", headers=auth(), json={
        "title": "Bad Time",
        "start_time": (now + timedelta(days=2)).isoformat(),
        "end_time": (now + timedelta(days=1)).isoformat(),
    })
    assert r.status_code == 400


def test_create_activity_normalizes_vietnam_offset_to_utc(db_session):
    result = client.post("/activities", headers=auth(), json={
        "title": "Giờ Việt Nam",
        "start_time": "2027-06-15T18:30:00+07:00",
        "end_time": "2027-06-15T20:00:00+07:00",
    })
    assert result.status_code in (200, 201)
    activity = db_session.query(Activity).filter(Activity.id == result.json()["id"]).one()
    assert activity.start_time == datetime(2027, 6, 15, 11, 30)
    assert activity.end_time == datetime(2027, 6, 15, 13, 0)


def test_update_activity_normalizes_timezone_aware_datetime():
    activity_id = _create_activity()
    result = client.put(f"/activities/{activity_id}", headers=auth(), json={
        "start_time": "2027-06-15T18:30:00+07:00",
        "end_time": "2027-06-15T20:00:00+07:00",
    })
    assert result.status_code == 200
    assert result.json()["start_time"].startswith("2027-06-15T11:30:00")
    assert result.json()["end_time"].startswith("2027-06-15T13:00:00")


def test_list_and_get_activity():
    aid = _create_activity()
    lst = client.get("/activities", headers=auth())
    assert lst.status_code == 200
    ids = [a["id"] for a in lst.json()]
    assert aid in ids

    g = client.get(f"/activities/{aid}", headers=auth())
    assert g.status_code == 200
    assert g.json()["id"] == aid


def test_access_denied_for_attendance_create():
    # thanhvien should NOT be able to create attendance (only chu_nhiem/truong_ban)
    token = client.post("/auth/login", json={"username": "thanhvien", "password": "123456"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/attendance", headers=h, json={
        "activity_id": 999999,
        "member_id": 1,
        "status": "present",
    })
    assert r.status_code in (403, 404)
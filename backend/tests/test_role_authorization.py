"""Test phân quyền tính năng theo vai trò (Chủ nhiệm/Trưởng ban vs Thành viên)."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def token_of(username, password="123456"):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


def auth(username):
    return {"Authorization": f"Bearer {token_of(username)}"}


def _create_activity(admin="chunhiem", offset_minutes=-10):
    """Tạo hoạt động đang diễn ra (mặc định bắt đầu 10 phút trước)."""
    now = datetime.utcnow()
    start = now + timedelta(minutes=offset_minutes)
    resp = client.post(
        "/activities",
        headers=auth(admin),
        json={
            "title": "Hoạt động phân quyền",
            "description": "Test role guard",
            "location": "Hội trường C",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=2)).isoformat(),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# A. Chủ nhiệm & Trưởng ban: quản lý hoạt động + xem điểm danh
# ---------------------------------------------------------------------------

def test_leader_can_create_activity():
    assert _create_activity(admin="truongbantt")["id"]


def test_admin_can_update_and_delete_activity():
    activity = _create_activity()
    upd = client.put(
        f"/activities/{activity['id']}",
        headers=auth("chunhiem"),
        json={"title": "Đã đổi tên"},
    )
    assert upd.status_code == 200
    assert upd.json()["title"] == "Đã đổi tên"

    dele = client.delete(f"/activities/{activity['id']}", headers=auth("chunhiem"))
    assert dele.status_code == 204


def test_leader_can_view_attendee_list():
    activity = _create_activity()
    members = client.get("/members", headers=auth("chunhiem")).json()
    client.post(
        "/attendance",
        headers=auth("chunhiem"),
        json={"activity_id": activity["id"], "member_id": members[0]["id"], "status": "present"},
    )

    resp = client.get(f"/activities/{activity['id']}/attendees", headers=auth("truongbantt"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert "checked_at" in body["attendees"][0]
    assert "full_name" in body["attendees"][0]


def test_admin_can_export_attendee_csv():
    activity = _create_activity()
    resp = client.get(
        f"/activities/{activity['id']}/attendees/export", headers=auth("chunhiem")
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Họ tên" in resp.text


# ---------------------------------------------------------------------------
# B. Thành viên: bị ẩn / chặn các chức năng quản lý
# ---------------------------------------------------------------------------

def test_member_cannot_create_activity():
    now = datetime.utcnow()
    resp = client.post(
        "/activities",
        headers=auth("thanhvien"),
        json={
            "title": "Không được phép",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
        },
    )
    assert resp.status_code == 403


def test_member_cannot_update_or_delete_activity():
    activity = _create_activity()
    upd = client.put(
        f"/activities/{activity['id']}", headers=auth("thanhvien"), json={"title": "Hack"}
    )
    assert upd.status_code == 403
    dele = client.delete(f"/activities/{activity['id']}", headers=auth("thanhvien"))
    assert dele.status_code == 403


def test_member_cannot_view_attendee_list():
    activity = _create_activity()
    resp = client.get(f"/activities/{activity['id']}/attendees", headers=auth("thanhvien"))
    assert resp.status_code == 403


def test_member_cannot_view_registration_list():
    activity = _create_activity()
    resp = client.get(
        f"/activities/{activity['id']}/registrations", headers=auth("thanhvien")
    )
    assert resp.status_code == 403


def test_member_cannot_create_attendance_for_others():
    activity = _create_activity()
    members = client.get("/members", headers=auth("chunhiem")).json()
    resp = client.post(
        "/attendance",
        headers=auth("thanhvien"),
        json={"activity_id": activity["id"], "member_id": members[0]["id"], "status": "present"},
    )
    assert resp.status_code == 403


def test_member_only_sees_own_attendance_records():
    activity = _create_activity()
    members = client.get("/members", headers=auth("chunhiem")).json()
    # Chủ nhiệm điểm danh hộ 2 thành viên khác nhau
    for member in members[:2]:
        client.post(
            "/attendance",
            headers=auth("chunhiem"),
            json={"activity_id": activity["id"], "member_id": member["id"], "status": "present"},
        )

    mine = client.get("/attendance", headers=auth("thanhvien")).json()
    own_member_id = client.get("/auth/me", headers=auth("thanhvien")).json()["member_id"]
    assert mine, "Thành viên phải xem được bản ghi của chính mình"
    assert all(row["member_id"] == own_member_id for row in mine)


def test_member_cannot_access_admin_only_ai_features():
    activity = _create_activity()
    resp = client.post(
        "/ai/notifications", headers=auth("thanhvien"), json={"activity_id": activity["id"]}
    )
    assert resp.status_code == 403


def test_member_cannot_view_top_members_stats():
    resp = client.get("/stats/members/top", headers=auth("thanhvien"))
    assert resp.status_code == 403
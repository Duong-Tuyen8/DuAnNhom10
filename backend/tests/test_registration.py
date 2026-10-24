"""Test luồng đăng ký tham gia & tự điểm danh của Thành viên."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PNG_PROOF = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def token_of(username, password="123456"):
    return client.post(
        "/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]


def auth(username):
    return {"Authorization": f"Bearer {token_of(username)}"}


def _make_activity(offset_minutes=-10, duration_hours=2, title="Hoạt động đăng ký"):
    """Tạo hoạt động (mặc định đang diễn ra để cửa sổ điểm danh mở)."""
    now = datetime.utcnow()
    start = now + timedelta(minutes=offset_minutes)
    resp = client.post(
        "/activities",
        headers=auth("chunhiem"),
        json={
            "title": title,
            "description": "Test đăng ký / điểm danh",
            "location": "Phòng D101",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=duration_hours)).isoformat(),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Đăng ký tham gia
# ---------------------------------------------------------------------------

def test_member_can_register_for_activity():
    activity = _make_activity()
    resp = client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["activity_id"] == activity["id"]
    assert body["registration_count"] >= 1


def test_member_without_member_profile_can_join_and_profile_is_created_automatically():
    activity = _make_activity(title="Tài khoản thành viên chưa có hồ sơ")
    login = client.post(
        "/auth/oauth/demo",
        json={
            "provider": "google",
            "email": "auto-profile-member@test.vn",
            "name": "Thành viên tự động",
            "provider_user_id": "auto-profile-member-2026",
        },
    )
    assert login.status_code == 200, login.text
    assert login.json()["member_id"] is None
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    joined = client.post(f"/api/activities/{activity['id']}/join", headers=headers)
    assert joined.status_code == 201, joined.text
    assert joined.json()["member_id"] is not None

    detail = client.get(f"/activities/{activity['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["is_registered"] is True


def test_duplicate_registration_rejected():
    activity = _make_activity()
    first = client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert first.status_code == 201
    second = client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert second.status_code == 400


def test_member_can_unregister_before_check_in():
    activity = _make_activity(offset_minutes=60, title="Hoạt động hủy đăng ký")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    resp = client.delete(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert resp.status_code == 200
    # Hủy lần 2 phải báo chưa đăng ký
    again = client.delete(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert again.status_code == 404


def test_admin_cannot_use_member_self_registration():
    """Chủ nhiệm / Trưởng ban không dùng chức năng tự phục vụ của Thành viên."""
    activity = _make_activity()
    resp = client.post(f"/activities/{activity['id']}/register", headers=auth("chunhiem"))
    assert resp.status_code == 403


def test_activity_detail_shows_member_registration_state():
    activity = _make_activity()
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))

    detail = client.get(f"/activities/{activity['id']}", headers=auth("thanhvien")).json()
    assert detail["is_registered"] is True
    assert detail["my_attendance_status"] is None
    assert detail["registration_count"] >= 1


# ---------------------------------------------------------------------------
# Tự điểm danh (self check-in)
# ---------------------------------------------------------------------------

def test_check_in_requires_registration():
    activity = _make_activity(title="Chưa đăng ký đã điểm danh")
    resp = client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert resp.status_code == 400
    assert "đăng ký" in resp.json()["detail"]


def test_check_in_rejected_when_window_closed():
    activity = _make_activity(offset_minutes=180, title="Hoạt động chưa tới giờ")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    resp = client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert resp.status_code == 400
    assert "Chưa đến giờ điểm danh" in resp.json()["detail"]


def test_member_self_check_in_success():
    activity = _make_activity(title="Hoạt động điểm danh được")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))

    resp = client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"], "feedback": "Đúng giờ"},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "PENDING_CHECKIN"
    assert body["feedback"] == "Đúng giờ"
    assert body["proof_image_url"].startswith("/attendance/proofs/")
    assert body["checked_in_at"]

    # Điểm danh lần 2 phải bị chặn
    again = client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert again.status_code == 400


def test_cannot_unregister_after_check_in():
    activity = _make_activity(title="Không hủy được sau điểm danh")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    resp = client.delete(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    assert resp.status_code == 400


def test_registration_status_endpoint():
    activity = _make_activity(title="Kiểm tra trạng thái đăng ký")
    status = client.get(
        f"/activities/{activity['id']}/registration-status", headers=auth("thanhvien")
    )
    assert status.status_code == 200
    body = status.json()
    assert body["is_registered"] is False
    assert body["can_register"] is True
    assert body["check_in_open"] is True

    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    after = client.get(
        f"/activities/{activity['id']}/registration-status", headers=auth("thanhvien")
    ).json()
    assert after["is_registered"] is True
    assert after["can_check_in"] is True


def test_registration_creates_complete_member_profile_visible_to_leaders():
    response = client.post(
        "/auth/register",
        json={
            "username": "profile_member_2026",
            "password": "pass123",
            "full_name": "Nguyễn Thành Viên Hồ Sơ",
            "date_of_birth": "2004-08-19",
            "gender": "Khác",
            "class_name": "CNTT-K16A",
            "department": "Công nghệ thông tin",
        },
    )
    assert response.status_code == 200, response.text
    member_id = response.json()["member_id"]
    assert member_id is not None

    members = client.get("/members", headers=auth("truongbantt"))
    assert members.status_code == 200
    profile = next(member for member in members.json() if member["id"] == member_id)
    assert profile["full_name"] == "Nguyễn Thành Viên Hồ Sơ"
    assert profile["date_of_birth"] == "2004-08-19"
    assert profile["gender"] == "Khác"
    assert profile["class_name"] == "CNTT-K16A"
    assert profile["department"] == "Công nghệ thông tin"
    assert profile["joined_date"]


def test_member_cannot_view_member_list_or_activity_participants():
    activity = _make_activity(title="Riêng tư danh sách thành viên")
    assert client.get("/members", headers=auth("thanhvien")).status_code == 403
    member_participants = client.get(
        f"/activities/{activity['id']}/participants",
        headers=auth("thanhvien"),
    )
    assert member_participants.status_code == 200
    assert len(member_participants.json()["not_joined"]) >= 1
    participants = client.get(
        f"/activities/{activity['id']}/participants",
        headers=auth("truongbantt"),
    )
    assert participants.status_code == 200, participants.text


def test_join_and_checkin_activity_aliases_work():
    activity = _make_activity(title="Tham gia qua alias")
    joined = client.post(
        f"/activities/{activity['id']}/join",
        headers=auth("thanhvien"),
    )
    assert joined.status_code == 201, joined.text

    checked_in = client.post(
        f"/activities/{activity['id']}/checkin",
        headers=auth("thanhvien"),
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert checked_in.status_code == 201, checked_in.text
    assert checked_in.json()["status"] == "PENDING_CHECKIN"
    assert checked_in.json()["checked_at"]


def test_my_attendance_history():
    activity = _make_activity(title="Lịch sử điểm danh của tôi")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )

    resp = client.get("/attendance/me", headers=auth("thanhvien"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    titles = [row["activity_title"] for row in body["attendances"]]
    assert "Lịch sử điểm danh của tôi" in titles


def test_admin_sees_registration_list():
    activity = _make_activity(title="Danh sách đăng ký cho ban quản lý")
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))

    resp = client.get(f"/activities/{activity['id']}/registrations", headers=auth("chunhiem"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert any(r["checked_in"] is False for r in body["registrations"])


def test_admin_can_review_proof_and_member_can_resubmit_after_rejection():
    activity = _make_activity(title="Duyệt minh chứng")
    client.post(f"/activities/{activity['id']}/join", headers=auth("thanhvien"))
    submitted = client.post(
        f"/api/activities/{activity['id']}/checkin",
        headers=auth("thanhvien"),
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert submitted.status_code == 201, submitted.text
    member_id = submitted.json()["member_id"]
    activity_row = next(
        row for row in client.get("/stats/activities", headers=auth("chunhiem")).json()
        if row["id"] == activity["id"]
    )
    assert activity_row["attendance_count"] == 0

    details = client.get(
        f"/api/activities/{activity['id']}/participants",
        headers=auth("chunhiem"),
    ).json()
    pending = next(row for row in details["registered"] if row["member_id"] == member_id)
    assert pending["status"] == "PENDING_CHECKIN"
    assert pending["proof_image_url"]
    proof_response = client.get(pending["proof_image_url"], headers=auth("chunhiem"))
    assert proof_response.status_code == 200
    assert client.get(pending["proof_image_url"], headers=auth("thanhvien")).status_code == 403
    queue = client.get("/api/attendance/pending", headers=auth("chunhiem"))
    assert queue.status_code == 200
    pending_row = next(row for row in queue.json()["attendances"] if row["member_id"] == member_id)
    assert pending_row["class_name"] == ""
    assert pending_row["department"] == ""

    rejected = client.patch(
        f"/api/attendance/{pending_row['id']}/verify",
        headers=auth("chunhiem"),
        json={"status": "REJECTED", "reject_reason": "Ảnh chưa rõ"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "REJECTED"
    assert rejected.json()["reject_reason"] == "Ảnh chưa rõ"

    resubmitted = client.post(
        f"/activities/{activity['id']}/checkin",
        headers=auth("thanhvien"),
        files={"photo": ("proof.png", PNG_PROOF, "image/png")},
    )
    assert resubmitted.status_code == 201, resubmitted.text
    assert resubmitted.json()["status"] == "PENDING_CHECKIN"

    resubmitted_id = resubmitted.json()["id"]
    approved = client.patch(
        f"/api/attendance/{resubmitted_id}/verify",
        headers=auth("truongbantt"),
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "ATTENDED"
    assert approved.json()["verified_by"]
    assert approved.json()["verified_at"]
    activity_row = next(
        row for row in client.get("/stats/activities", headers=auth("chunhiem")).json()
        if row["id"] == activity["id"]
    )
    assert activity_row["attendance_count"] == 1

    member_details = client.get(
        f"/activities/{activity['id']}/participants",
        headers=auth("thanhvien"),
    ).json()
    assert any(row["member_id"] == member_id for row in member_details["attended"])
    assert all("proof_image_url" not in row for row in member_details["registered"])


def test_check_in_requires_valid_image_and_moderator_only_can_verify():
    activity = _make_activity(title="Từ chối file không phải ảnh")
    client.post(f"/activities/{activity['id']}/join", headers=auth("thanhvien"))
    invalid = client.post(
        f"/activities/{activity['id']}/checkin",
        headers=auth("thanhvien"),
        files={"photo": ("not-image.txt", b"not an image", "text/plain")},
    )
    assert invalid.status_code == 400

    no_photo = client.post(
        f"/activities/{activity['id']}/checkin",
        headers=auth("thanhvien"),
    )
    assert no_photo.status_code == 422

    denied = client.patch(
        f"/activities/{activity['id']}/verify-attendance",
        headers=auth("thanhvien"),
        json={"member_id": 3, "action": "approve"},
    )
    assert denied.status_code == 403


def test_admin_can_export_full_attendance_report():
    resp = client.get("/attendance/export", headers=auth("truongbantt"))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Hoạt động" in resp.text
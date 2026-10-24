from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from app.main import app
from app.models import Activity, Attendance, Member, Registration

client = TestClient(app)


def get_admin_token():
    response = client.post("/auth/login", json={"username": "chunhiem", "password": "123456"})
    return response.json()["access_token"]


def admin_headers():
    return {"Authorization": f"Bearer {get_admin_token()}"}


def test_ai_notification_generation():
    activities = client.get("/activities", headers=admin_headers()).json()
    assert len(activities) > 0
    aid = activities[0]["id"]
    before = client.get("/notifications", headers=admin_headers()).json()

    r = client.post("/ai/notifications", headers=admin_headers(), json={"activity_id": aid})
    assert r.status_code == 200
    data = r.json()
    assert data["notification"]["is_ai_generated"] == True
    assert data["notification"]["id"] is None
    assert len(data["notification"]["content"]) > 10
    assert client.get("/notifications", headers=admin_headers()).json() == before

    published = client.post("/notifications", headers=admin_headers(), json={
        "title": "Biên tập xong",
        "content": "Nội dung đã được quản lý chỉnh sửa.",
        "activity_id": aid,
        "is_ai_generated": True,
    })
    assert published.status_code == 201
    assert published.json()["is_ai_generated"] is True
    created_at = datetime.fromisoformat(published.json()["created_at"])
    assert abs((datetime.utcnow() - created_at).total_seconds()) < 10


def test_ai_notification_formats_activity_time_in_vietnam_timezone(db_session):
    activity = Activity(
        title="Sự kiện giờ Việt Nam",
        start_time=datetime(2027, 6, 15, 11, 30),
        end_time=datetime(2027, 6, 15, 13, 0),
    )
    db_session.add(activity)
    db_session.commit()

    result = client.post(
        "/ai/notifications",
        headers=admin_headers(),
        json={"activity_id": activity.id},
    )
    assert result.status_code == 200
    prompt = result.json()["prompt"]
    assert "Thời gian: 18:30 15/06/2027 đến 20:00 15/06/2027" in prompt


def test_ai_notification_draft_for_unsaved_activity_does_not_persist():
    result = client.post("/ai/notifications", headers=admin_headers(), json={
        "title": "Hoạt động chưa lưu",
        "description": "Nội dung tóm tắt",
        "location": "Hội trường",
        "start_time": "Thứ Sáu, 18:00",
        "end_time": "Thứ Sáu, 20:00",
    })
    assert result.status_code == 200
    assert result.json()["notification"]["id"] is None
    assert "Hoạt động chưa lưu" in result.json()["notification"]["content"]


def test_ai_summary_generation(db_session):
    now = datetime.utcnow()
    activity = Activity(
        title="Hoạt động đã kết thúc",
        description="Buổi chia sẻ kỹ thuật",
        location="Phòng A",
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=1),
        notes="Ban tổ chức ghi nhận phần thảo luận sôi nổi.",
    )
    db_session.add(activity)
    db_session.commit()
    member = db_session.query(Member).filter(Member.student_id == "SV001").one()
    db_session.add(Registration(activity_id=activity.id, member_id=member.id))
    db_session.add(Attendance(
        activity_id=activity.id,
        member_id=member.id,
        status="ATTENDED",
        feedback="Nội dung hữu ích",
        proof_image_url="/attendance/proofs/proof.png",
    ))
    db_session.commit()
    aid = activity.id
    r = client.post("/ai/summaries", headers=admin_headers(), json={"activity_id": aid})
    assert r.status_code == 200
    data = r.json()
    assert len(data["summary"]) > 10
    assert data["activity_id"] == aid
    assert data["registration_count"] == 1
    assert data["attendee_count"] == 1
    assert data["feedback_count"] == 1
    assert data["proof_count"] == 1
    assert "Điểm tích cực" in data["summary"]
    assert "Vấn đề cần cải thiện" in data["summary"]


def test_ai_summary_rejects_upcoming_activity():
    activities = client.get("/activities", headers=admin_headers()).json()
    result = client.post(
        "/ai/summaries",
        headers=admin_headers(),
        json={"activity_id": activities[0]["id"]},
    )
    assert result.status_code == 400


def test_ai_notification_missing_activity():
    r = client.post("/ai/notifications", headers=admin_headers(), json={"activity_id": 999999})
    assert r.status_code == 404


def test_ai_forbidden_for_member():
    # Member cannot use AI
    r = client.post("/auth/login", json={"username": "thanhvien", "password": "123456"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    activities = client.get("/activities", headers=admin_headers()).json()
    if activities:
        r2 = client.post("/ai/summaries", headers=h, json={"activity_id": activities[0]["id"]})
        assert r2.status_code in (403, 404)


def test_member_activity_recommendations_are_personalized_and_exclude_registered(db_session):
    now = datetime.utcnow()
    days_until_friday = (4 - now.weekday()) % 7 + 1
    friday = now + timedelta(days=days_until_friday)
    available = Activity(
        title="Workshop kỹ thuật",
        description="Thực hành IT",
        location="Phòng máy",
        start_time=friday,
        end_time=friday + timedelta(hours=2),
    )
    registered = Activity(
        title="Buổi sinh hoạt chung",
        description="Gặp mặt thành viên",
        location="Hội trường",
        start_time=friday + timedelta(days=1),
        end_time=friday + timedelta(days=1, hours=2),
    )
    db_session.add_all([available, registered])
    db_session.commit()
    member = db_session.query(Member).filter(Member.student_id == "SV003").one()
    db_session.add(Registration(activity_id=registered.id, member_id=member.id))
    db_session.commit()

    login = client.post("/auth/login", json={"username": "thanhvien", "password": "123456"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    result = client.get("/ai/activity-recommendations", headers=headers)
    assert result.status_code == 200
    recommendations = result.json()["recommendations"]
    assert len(recommendations) <= 5
    assert any(item["activity_id"] == available.id for item in recommendations)
    assert all(item["activity_id"] != registered.id for item in recommendations)
    preferred = next(item for item in recommendations if item["activity_id"] == available.id)
    assert "kỹ thuật" in preferred["reason"].lower() or "ky thuat" in preferred["reason"].lower()


def test_activity_recommendations_forbidden_for_manager():
    result = client.get("/ai/activity-recommendations", headers=admin_headers())
    assert result.status_code == 403


def test_task_assignment_ai_endpoint_is_not_exposed():
    result = client.post("/ai/assignments", headers=admin_headers(), json={
        "activity_id": 1,
        "task_descriptions": ["Chuẩn bị địa điểm"],
    })
    assert result.status_code in (404, 405)
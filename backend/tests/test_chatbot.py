"""Test AI Chatbot: RAG context, hỏi đáp, streaming và phân quyền."""
import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def token_of(username, password="123456"):
    return client.post(
        "/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]


def auth(username):
    return {"Authorization": f"Bearer {token_of(username)}"}


def _make_activity(title, offset_minutes=-10, duration_hours=2, location="Hội trường E"):
    """Tạo hoạt động (mặc định đang diễn ra hôm nay)."""
    now = datetime.utcnow()
    start = now + timedelta(minutes=offset_minutes)
    resp = client.post(
        "/activities",
        headers=auth("chunhiem"),
        json={
            "title": title,
            "description": "Hoạt động phục vụ test chatbot",
            "location": location,
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=duration_hours)).isoformat(),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def ask(question, username="thanhvien", history=None):
    payload = {"message": question}
    if history:
        payload["history"] = history
    resp = client.post("/api/chat", headers=auth(username), json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Endpoint cơ bản
# ---------------------------------------------------------------------------

def test_chat_requires_authentication():
    resp = client.post("/api/chat", json={"message": "Hôm nay có hoạt động nào?"})
    assert resp.status_code in (401, 403)


def test_chat_suggestions():
    resp = client.get("/api/chat/suggestions", headers=auth("thanhvien"))
    assert resp.status_code == 200
    suggestions = resp.json()["suggestions"]
    assert any("Hôm nay" in s for s in suggestions)
    assert any("điểm danh" in s for s in suggestions)


def test_chat_context_preview_returns_db_data():
    _make_activity("Chatbot: Hoạt động hôm nay", offset_minutes=-5)
    resp = client.get(
        "/api/chat/context",
        headers=auth("thanhvien"),
        params={"question": "Hôm nay có hoạt động nào?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"]
    context = body["context"]
    assert context["today"], "Phải tìm thấy hoạt động diễn ra hôm nay"
    assert context["user"]["username"] == "thanhvien"


# ---------------------------------------------------------------------------
# Kịch bản truy vấn mẫu (theo yêu cầu)
# ---------------------------------------------------------------------------

def test_chat_today_question():
    activity = _make_activity("Chatbot: Workshop sáng nay", offset_minutes=-5)
    result = ask("Hôm nay có các hoạt động nào?")
    assert result["reply"]
    assert activity["title"] in result["reply"]
    assert result["context"]["today_count"] >= 1


def test_chat_week_question():
    _make_activity("Chatbot: Sự kiện tuần này", offset_minutes=60 * 24 * 2)
    result = ask("Tuần này có sự kiện gì không?")
    assert "Chatbot: Sự kiện tuần này" in result["reply"] or "7 ngày tới" in result["reply"]


def test_chat_location_and_time_question():
    activity = _make_activity(
        "Chatbot: Tọa đàm kỹ năng mềm", offset_minutes=120, location="Giảng đường F1"
    )
    result = ask("Hoạt động Tọa đàm kỹ năng mềm diễn ra ở đâu, mấy giờ?")
    assert result["reply"]
    # Câu trả lời phải chứa địa điểm thật lấy từ DB
    assert "Giảng đường F1" in result["reply"]
    assert result["context"]["matched_count"] >= 1
    assert activity["id"]


def test_chat_attendance_question_before_check_in():
    activity = _make_activity("Chatbot: Buổi sinh hoạt chuyên môn", offset_minutes=-5)
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))

    result = ask("Tôi đã điểm danh hoạt động Buổi sinh hoạt chuyên môn chưa?")
    assert "chưa điểm danh" in result["reply"].lower()


def test_chat_attendance_question_after_check_in():
    activity = _make_activity("Chatbot: Hoạt động đã điểm danh", offset_minutes=-5)
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))
    client.post(
        "/attendance/check-in",
        headers=auth("thanhvien"),
        data={"activity_id": activity["id"]},
        files={"photo": ("proof.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32, "image/png")},
    )

    result = ask("Tôi đã điểm danh hoạt động Hoạt động đã điểm danh chưa?")
    assert "chờ duyệt" in result["reply"].lower()
    assert result["context"]["my_attendances"] >= 1


def test_chat_registration_question():
    activity = _make_activity("Chatbot: Hoạt động đã đăng ký", offset_minutes=180)
    client.post(f"/activities/{activity['id']}/register", headers=auth("thanhvien"))

    result = ask("Tôi đã đăng ký hoạt động nào?")
    assert "Chatbot: Hoạt động đã đăng ký" in result["reply"]


def test_chat_empty_message_returns_guidance():
    resp = client.post("/api/chat", headers=auth("thanhvien"), json={"message": "   "})
    assert resp.status_code == 200
    assert "nhập câu hỏi" in resp.json()["reply"]


def test_chat_accepts_history():
    history = [
        {"role": "user", "content": "Hôm nay có hoạt động nào?"},
        {"role": "assistant", "content": "Để mình kiểm tra nhé."},
    ]
    result = ask("Tuần này có sự kiện gì không?", history=history)
    assert result["reply"]


# ---------------------------------------------------------------------------
# Streaming (Server-Sent Events)
# ---------------------------------------------------------------------------

def test_chat_stream_returns_sse_events():
    _make_activity("Chatbot: Hoạt động streaming", offset_minutes=-5)
    with client.stream(
        "POST",
        "/api/chat/stream",
        headers=auth("thanhvien"),
        json={"message": "Hôm nay có hoạt động nào?"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join(response.iter_text())

    events = [
        json.loads(line[len("data: "):])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    assert events, "Phải có ít nhất một event SSE"
    assert events[0]["type"] == "meta"
    assert events[-1]["type"] == "done"
    assert any(event["type"] == "delta" for event in events)

    reply = "".join(event["text"] for event in events if event["type"] == "delta")
    assert "Chatbot: Hoạt động streaming" in reply


def test_chat_works_for_admin_role_too():
    _make_activity("Chatbot: Hoạt động cho ban quản lý", offset_minutes=-5)
    result = ask("Hôm nay có hoạt động nào?", username="chunhiem")
    assert result["reply"]
    assert result["context"]["today_count"] >= 1
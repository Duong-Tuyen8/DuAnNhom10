"""Xây dựng ngữ cảnh (context) từ Database để làm dữ liệu cho AI Chatbot (RAG).

Khi người dùng hỏi, Backend truy vấn dữ liệu hoạt động thực tế (theo thời gian)
và trạng thái của chính người dùng, rồi đưa vào prompt để AI trả lời chính xác.
"""
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import (
    ROLE_LABELS,
    Activity,
    Attendance,
    Committee,
    Member,
    Registration,
    Task,
    User,
)
from ..activity_helpers import APPROVED_ATTENDANCE_STATUSES, STATUS_LABELS, is_check_in_open

WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

# Từ dừng tiếng Việt (đã bỏ dấu) để tách từ khóa tìm hoạt động từ câu hỏi
STOPWORDS = {
    "hom", "nay", "tuan", "co", "gi", "khong", "nao", "o", "dau", "may", "gio",
    "toi", "da", "diem", "danh", "chua", "hoat", "dong", "su", "kien", "the",
    "la", "va", "cua", "cho", "minh", "ban", "em", "cac", "nhung", "hay",
    "khi", "duoc", "se", "ngay", "thang", "lich", "sach", "thong", "tin",
    "chi", "tiet", "gioi", "thieu", "xay", "ra", "to", "chuc", "ai", "tro",
    "ly", "giup", "hoi", "muon", "biet", "xem", "trong", "tai", "vay", "thi",
}


def _fmt(dt: Optional[datetime]) -> str:
    if not dt:
        return "chưa xác định"
    return f"{WEEKDAYS_VI[dt.weekday()]}, {dt.strftime('%d/%m/%Y %H:%M')}"


def _normalize(text: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp từ khóa dễ hơn."""
    import unicodedata

    text = (text or "").lower().replace("đ", "d")
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    )


def _keywords(question: str) -> List[str]:
    tokens = _normalize(question)
    tokens = "".join(ch if ch.isalnum() else " " for ch in tokens)
    return [w for w in tokens.split() if len(w) >= 3 and w not in STOPWORDS]


def _activity_brief(db: Session, activity: Activity) -> Dict[str, Any]:
    registration_count = (
        db.query(Registration).filter(Registration.activity_id == activity.id).count()
    )
    attendee_count = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        )
        .count()
    )
    return {
        "id": activity.id,
        "title": activity.title,
        "description": activity.description or "",
        "location": activity.location or "chưa cập nhật",
        "start_text": _fmt(activity.start_time),
        "end_text": _fmt(activity.end_time),
        "registration_count": registration_count,
        "attendee_count": attendee_count,
        "check_in_window": "đang mở" if is_check_in_open(activity) else "chưa mở",
        "notes": activity.notes or "",
    }


def _match_activities(question: str, activities: List[Activity]) -> List[Activity]:
    """Tìm hoạt động có tên gần với câu hỏi (từ khóa + độ tương đồng chuỗi)."""
    words = _keywords(question)
    if not words:
        return []

    normalized_question = _normalize(question)
    scored = []
    for activity in activities:
        title_norm = _normalize(activity.title)
        score = 0.0
        for word in words:
            if word in title_norm:
                score += 2.0
        score += SequenceMatcher(None, normalized_question, title_norm).ratio()
        if score > 1.0:
            scored.append((score, activity))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [activity for _, activity in scored[:3]]


def build_context(db: Session, current_user: User, question: str) -> Dict[str, Any]:
    """Truy vấn DB và dựng context (RAG) để đưa vào prompt của AI."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)

    all_activities = db.query(Activity).order_by(Activity.start_time.asc()).all()

    today = [
        a for a in all_activities if a.start_time and today_start <= a.start_time < today_end
    ]
    this_week = [
        a
        for a in all_activities
        if a.start_time and today_start <= a.start_time < week_end and a not in today
    ]
    upcoming = [a for a in all_activities if a.end_time and a.end_time >= now][:10]
    recent = [a for a in all_activities if a.end_time and a.end_time < now][-5:]
    matched = _match_activities(question, all_activities)

    # ---- Thông tin người dùng & trạng thái cá nhân ----
    member = (
        db.query(Member).filter(Member.id == current_user.member_id).first()
        if current_user.member_id
        else None
    )
    committee_name = ""
    if member and member.committee_id:
        committee = db.query(Committee).filter(Committee.id == member.committee_id).first()
        committee_name = committee.name if committee else ""

    my_registrations = []
    my_attendances = []
    my_tasks = []

    if member:
        registrations = (
            db.query(Registration)
            .filter(Registration.member_id == member.id)
            .order_by(Registration.created_at.desc())
            .all()
        )
        for reg in registrations:
            activity = next((a for a in all_activities if a.id == reg.activity_id), None)
            if not activity:
                continue
            attendance = (
                db.query(Attendance)
                .filter(
                    Attendance.activity_id == activity.id,
                    Attendance.member_id == member.id,
                )
                .first()
            )
            my_registrations.append(
                {
                    "activity_id": activity.id,
                    "activity_title": activity.title,
                    "start_text": _fmt(activity.start_time),
                    "location": activity.location or "chưa cập nhật",
                    "checked_in": bool(
                        attendance and attendance.status in APPROVED_ATTENDANCE_STATUSES
                    ),
                    "attendance_status": attendance.status if attendance else None,
                }
            )

        records = (
            db.query(Attendance)
            .filter(Attendance.member_id == member.id)
            .order_by(Attendance.checked_at.desc())
            .limit(15)
            .all()
        )
        for r in records:
            activity = next((a for a in all_activities if a.id == r.activity_id), None)
            my_attendances.append(
                {
                    "activity_id": r.activity_id,
                    "activity_title": activity.title if activity else "N/A",
                    "start_text": _fmt(activity.start_time) if activity else "",
                    "status": r.status,
                    "status_label": STATUS_LABELS.get(r.status, r.status),
                    "feedback": r.feedback or "",
                    "checked_at": r.checked_at.isoformat() if r.checked_at else None,
                }
            )

        tasks = (
            db.query(Task)
            .filter(Task.assignee_id == member.id)
            .order_by(Task.created_at.desc())
            .limit(10)
            .all()
        )
        my_tasks = [
            {"title": t.title, "status": t.status, "priority": t.priority} for t in tasks
        ]

    return {
        "now_text": _fmt(now),
        "today_text": today_start.strftime("%d/%m/%Y"),
        "today": [_activity_brief(db, a) for a in today],
        "this_week": [_activity_brief(db, a) for a in this_week],
        "upcoming": [_activity_brief(db, a) for a in upcoming],
        "recent": [_activity_brief(db, a) for a in recent],
        "matched_activities": [_activity_brief(db, a) for a in matched],
        "total_activities": len(all_activities),
        "user": {
            "username": current_user.username,
            "role": current_user.role,
            "role_label": ROLE_LABELS.get(current_user.role, current_user.role),
            "member_id": current_user.member_id,
            "member_name": member.full_name if member else None,
            "student_id": member.student_id if member else None,
            "committee_name": committee_name,
        },
        "my_registrations": my_registrations,
        "my_attendances": my_attendances,
        "my_tasks": my_tasks,
    }
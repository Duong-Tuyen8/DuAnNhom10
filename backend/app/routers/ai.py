import re
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Activity, User, Attendance, Registration
from ..schemas import AINotificationRequest, AISummaryRequest
from ..security import ensure_member_profile, is_member, require_roles
from ..activity_helpers import APPROVED_ATTENDANCE_STATUSES
from ..ai import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])
VIETNAM_TIMEZONE = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")


def _get_activity(db: Session, activity_id: int) -> Activity:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    return activity


def _activity_info(activity: Activity) -> dict:
    def vietnam_datetime(value: datetime) -> str:
        utc_value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return utc_value.astimezone(VIETNAM_TIMEZONE).strftime("%H:%M %d/%m/%Y")

    return {
        "title": activity.title,
        "description": activity.description or "",
        "location": activity.location or "",
        "start_time": vietnam_datetime(activity.start_time) if activity.start_time else "",
        "end_time": vietnam_datetime(activity.end_time) if activity.end_time else "",
    }


@router.post("/notifications")
def ai_generate_notification(
    data: AINotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    """Tạo bản nháp thông báo; việc phát hành luôn do quản lý xác nhận."""
    activity = _get_activity(db, data.activity_id) if data.activity_id is not None else None
    if activity:
        info = _activity_info(activity)
    else:
        if not (data.title or "").strip():
            raise HTTPException(status_code=422, detail="Cần tên hoạt động để tạo thông báo")
        info = {
            "title": data.title.strip(),
            "description": data.description or "",
            "location": data.location or "",
            "start_time": data.start_time or "",
            "end_time": data.end_time or "",
        }
    prompt = ai_service.build_notification_prompt(info, current_user.role)
    content = ai_service.generate_text(prompt)
    return {
        "notification": {
            "id": None,
            "title": f"Thông báo: {info['title']}",
            "content": content,
            "is_ai_generated": True,
        },
        "prompt": prompt,
        "provider": ai_service.PROVIDER,
    }


@router.post("/summaries")
def ai_generate_summary(
    data: AISummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem", "truong_ban")),
):
    """AI tóm tắt kết quả hoạt động từ ghi chú và phản hồi."""
    activity = _get_activity(db, data.activity_id)
    if activity.end_time > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Chỉ có thể tóm tắt sau khi hoạt động kết thúc")
    info = _activity_info(activity)

    registrations_count = (
        db.query(Registration)
        .filter(Registration.activity_id == activity.id)
        .count()
    )
    attendances = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        )
        .all()
    )
    attendee_count = len(attendances)
    feedbacks = [a.feedback for a in attendances if a.feedback and a.feedback.strip()]
    proof_count = sum(1 for attendance in attendances if attendance.proof_image_url)

    notes = activity.notes or ""
    if proof_count:
        notes += f"\nSố lượt có ảnh minh chứng điểm danh đã duyệt: {proof_count}."
    prompt = ai_service.build_summary_prompt(
        info,
        notes,
        feedbacks,
        attendee_count,
        registrations_count=registrations_count,
    )
    content = ai_service.generate_text(prompt)

    return {
        "activity_id": activity.id,
        "activity_title": activity.title,
        "summary": content,
        "registration_count": registrations_count,
        "attendee_count": attendee_count,
        "feedback_count": len(feedbacks),
        "proof_count": proof_count,
        "prompt": prompt,
        "provider": ai_service.PROVIDER,
    }


@router.get("/activity-recommendations")
def recommend_activities(
    limit: int = Query(default=5, ge=3, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Recommend upcoming, unregistered activities using the member profile."""
    member = ensure_member_profile(db, current_user)
    now = datetime.utcnow()
    registered_ids = {
        row[0]
        for row in db.query(Registration.activity_id)
        .filter(Registration.member_id == member.id)
        .all()
    }
    activities = (
        db.query(Activity)
        .filter(Activity.start_time >= now)
        .order_by(Activity.start_time.asc())
        .all()
    )
    skills = [
        (skill.strip(), _normalized_text(skill.strip()))
        for skill in re.split(r"[,;|]", member.skills or "")
        if skill.strip()
    ]
    available_days = _available_weekdays(member.free_time or "")
    recommendations = []
    weekday_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

    for activity in activities:
        if activity.id in registered_ids:
            continue
        activity_text = _normalized_text(
            " ".join((activity.title or "", activity.description or "", activity.location or ""))
        )
        matched_skills = sorted(
            original
            for original, normalized in skills
            if len(normalized) >= 2
            and re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", activity_text)
        )
        # Activity times are stored as UTC; member schedules use Vietnam local weekdays.
        day_number = (activity.start_time + timedelta(hours=7)).isoweekday()
        schedule_match = day_number in available_days if available_days else None
        score = len(matched_skills) * 3 + (2 if schedule_match else 0)
        reasons = []
        if matched_skills:
            reasons.append(f"Kỹ năng phù hợp: {', '.join(matched_skills)}")
        if schedule_match:
            reasons.append(f"Thời gian phù hợp với lịch rảnh ({weekday_names[day_number - 1]})")
        elif schedule_match is False:
            reasons.append(f"Thời gian chưa khớp lịch rảnh đã khai báo ({weekday_names[day_number - 1]})")
        if not reasons:
            reasons.append("Hoạt động sắp diễn ra; hồ sơ kỹ năng hoặc lịch rảnh chưa đủ chi tiết để cá nhân hóa thêm")
        recommendations.append({
            "activity_id": activity.id,
            "title": activity.title,
            "start_time": activity.start_time,
            "end_time": activity.end_time,
            "location": activity.location or "",
            "reason": ". ".join(reasons) + ".",
            "score": score,
        })

    recommendations.sort(key=lambda item: (-item["score"], item["start_time"]))
    return {"recommendations": recommendations[:limit], "provider": "profile-match"}


def _normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _available_weekdays(value: str) -> set[int]:
    normalized = _normalized_text(value)
    days = {int(day) - 1 for day in re.findall(r"\bt\s*([2-7])\b", normalized)}
    if re.search(r"\b(cn|chu nhat)\b", normalized):
        days.add(7)
    weekday_names = {
        "thu hai": 1, "thu ba": 2, "thu tu": 3, "thu nam": 4,
        "thu sau": 5, "thu bay": 6,
    }
    for label, day in weekday_names.items():
        if label in normalized:
            days.add(day)
    return days
"""Helper dùng chung cho hoạt động, đăng ký tham gia và điểm danh.

Tách riêng để `routers/activities.py` và `routers/attendance.py` cùng dùng
một nguồn logic duy nhất (tránh lệch quy tắc nghiệp vụ).
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .models import Activity, Attendance, Member, Registration

# Cửa sổ điểm danh: mở trước giờ bắt đầu 30 phút và đóng khi hoạt động kết thúc.
CHECK_IN_OPEN_BEFORE = timedelta(minutes=30)

STATUS_LABELS = {
    "present": "Có mặt",
    "absent": "Vắng",
    "late": "Đi muộn",
    "REGISTERED": "Đã tham gia",
    "PENDING_CHECKIN": "Chờ duyệt điểm danh",
    "pending": "Chờ duyệt điểm danh",
    "ATTENDED": "Đã điểm danh",
    "REJECTED": "Bị từ chối điểm danh",
    "rejected": "Bị từ chối điểm danh",
}

APPROVED_ATTENDANCE_STATUSES = {"ATTENDED", "present", "late"}


def activity_out_payload(db: Session, activity: Activity, current_user=None) -> dict:
    """Dựng payload cho `ActivityOut`, kèm trạng thái của người dùng hiện tại.

    - `registration_count`: số thành viên đã đăng ký tham gia.
    - `is_registered`: người dùng hiện tại đã đăng ký chưa (chỉ với Thành viên).
    - `my_attendance_status` / `my_checked_at`: trạng thái điểm danh của chính họ.
    """
    attendee_count = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity.id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        )
        .count()
    )
    registration_count = (
        db.query(Registration).filter(Registration.activity_id == activity.id).count()
    )

    is_registered = False
    my_status = None
    my_checked_at = None
    my_reject_reason = ""
    can_check_in = False

    member_id = getattr(current_user, "member_id", None) if current_user else None
    if member_id:
        is_registered = (
            db.query(Registration)
            .filter(
                Registration.activity_id == activity.id,
                Registration.member_id == member_id,
            )
            .first()
            is not None
        )
        record = (
            db.query(Attendance)
            .filter(
                Attendance.activity_id == activity.id,
                Attendance.member_id == member_id,
            )
            .order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc())
            .first()
        )
        if record:
            my_status = record.status
            my_checked_at = record.checked_in_at or record.checked_at
            my_reject_reason = record.reject_reason or ""
        can_check_in = (
            is_check_in_open(activity)
            and (record is None or record.status in {"REJECTED", "rejected"})
        )

    return {
        "id": activity.id,
        "title": activity.title,
        "description": activity.description or "",
        "location": activity.location or "",
        "start_time": activity.start_time,
        "end_time": activity.end_time,
        "notes": activity.notes or "",
        "created_at": activity.created_at,
        "attendee_count": attendee_count,
        "registration_count": registration_count,
        "is_registered": is_registered,
        "my_attendance_status": my_status,
        "my_checked_at": my_checked_at,
        "my_reject_reason": my_reject_reason,
        "can_check_in": is_registered and can_check_in,
    }


def is_check_in_open(activity: Activity, now: Optional[datetime] = None) -> bool:
    """Điểm danh chỉ mở trong khoảng [start - 30 phút, end]."""
    now = now or datetime.utcnow()
    if not activity.start_time or not activity.end_time:
        return False
    return (activity.start_time - CHECK_IN_OPEN_BEFORE) <= now <= activity.end_time


def check_in_window_message(activity: Activity, now: Optional[datetime] = None) -> str:
    """Thông báo trạng thái cửa sổ điểm danh để hiển thị cho người dùng."""
    now = now or datetime.utcnow()
    if is_check_in_open(activity, now):
        return "Điểm danh đang mở"
    if activity.start_time and now < activity.start_time - CHECK_IN_OPEN_BEFORE:
        return "Chưa đến giờ điểm danh"
    return "Hoạt động đã kết thúc, không thể điểm danh"


def get_registration(
    db: Session, activity_id: int, member_id: int
) -> Optional[Registration]:
    return (
        db.query(Registration)
        .filter(
            Registration.activity_id == activity_id,
            Registration.member_id == member_id,
        )
        .first()
    )


def get_attendance(
    db: Session, activity_id: int, member_id: int
) -> Optional[Attendance]:
    return (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity_id,
            Attendance.member_id == member_id,
        )
        .order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc())
        .first()
    )


def registrations_payload(db: Session, activity_id: int) -> list:
    """Danh sách thành viên đã đăng ký tham gia một hoạt động."""
    records = (
        db.query(Registration)
        .filter(Registration.activity_id == activity_id)
        .order_by(Registration.created_at.asc())
        .all()
    )
    result = []
    for r in records:
        member = r.member or db.query(Member).filter(Member.id == r.member_id).first()
        attendance = get_attendance(db, activity_id, r.member_id)
        result.append(
            {
                "id": r.id,
                "activity_id": r.activity_id,
                "member_id": r.member_id,
                "member_name": member.full_name if member else "N/A",
                "student_id": member.student_id if member else "",
                "created_at": r.created_at,
                "checked_in": bool(attendance and attendance.status in APPROVED_ATTENDANCE_STATUSES),
                "attendance_status": attendance.status if attendance else None,
                "checked_at": (attendance.checked_in_at or attendance.checked_at) if attendance else None,
                "attendance_status_label": STATUS_LABELS.get(attendance.status, attendance.status) if attendance else None,
            }
        )
    return result


def attendees_payload(db: Session, activity_id: int) -> list:
    """Danh sách người dùng đã điểm danh (kèm thời gian điểm danh)."""
    records = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity_id,
            Attendance.status.in_(APPROVED_ATTENDANCE_STATUSES),
        )
        .order_by(Attendance.checked_in_at.desc(), Attendance.checked_at.desc())
        .all()
    )
    result = []
    for r in records:
        member = r.member or db.query(Member).filter(Member.id == r.member_id).first()
        result.append(
            {
                "member_id": r.member_id,
                "full_name": member.full_name if member else "N/A",
                "student_id": member.student_id if member else "",
                "class_name": member.class_name if member else "",
                "department": member.department if member else "",
                "status": r.status,
                "status_label": STATUS_LABELS.get(r.status, r.status),
                "feedback": r.feedback or "",
                "checked_at": r.checked_in_at or r.checked_at,
                "proof_image_url": r.proof_image_url,
            }
        )
    return result


def participants_payload(
    db: Session, activity_id: int, include_proofs: bool = False
) -> dict:
    """Chia toàn bộ thành viên CLB thành 3 nhóm cho 1 hoạt động.

    - attended: đã đăng ký + đã điểm danh (có checked_at).
    - registered: đã đăng ký nhưng chưa điểm danh.
    - not_joined: còn lại chưa nhấn Tham gia.
    Mỗi item gồm: member_id, full_name, class_name, department,
    status (ATTENDED/REGISTERED/NOT_JOINED), registered_at, attended_at.
    """
    registrations = (
        db.query(Registration)
        .filter(Registration.activity_id == activity_id)
        .order_by(Registration.created_at.asc())
        .all()
    )
    attendances = {
        a.member_id: a
        for a in db.query(Attendance)
        .filter(Attendance.activity_id == activity_id)
        .all()
    }
    attended, registered = [], []
    registered_ids = set()
    for r in registrations:
        member = r.member or db.query(Member).filter(Member.id == r.member_id).first()
        if not member:
            continue
        registered_ids.add(r.member_id)
        att = attendances.get(r.member_id)
        base = {
            "member_id": r.member_id,
            "full_name": member.full_name,
            "class_name": member.class_name or "",
            "department": member.department or "",
            "registered_at": r.created_at,
        }
        if att and att.status in APPROVED_ATTENDANCE_STATUSES:
            attended.append(
                {
                    **base,
                    "status": "ATTENDED",
                    "attended_at": att.checked_in_at or att.checked_at,
                    "attendance_status": att.status,
                }
            )
        else:
            participant = {
                **base,
                "status": att.status if att and att.status in {"PENDING_CHECKIN", "pending", "REJECTED", "rejected"} else "REGISTERED",
                "attended_at": None,
                "checked_in_at": (att.checked_in_at or att.checked_at) if att else None,
                "attendance_id": att.id if att else None,
                "reject_reason": att.reject_reason or "" if att else "",
            }
            if include_proofs and att:
                participant["proof_image_url"] = att.proof_image_url
            registered.append(participant)
    others = (
        db.query(Member)
        .filter(Member.is_active == True)  # noqa: E712
        .order_by(Member.full_name.asc())
        .all()
    )
    not_joined = [
        {
            "member_id": m.id,
            "full_name": m.full_name,
            "class_name": m.class_name or "",
            "department": m.department or "",
            "status": "NOT_JOINED",
            "registered_at": None,
            "attended_at": None,
        }
        for m in others
        if m.id not in registered_ids
    ]
    return {
        "attended": attended,
        "registered": registered,
        "not_joined": not_joined,
        "counts": {
            "attended": len(attended),
            "registered": len(registered),
            "pending_approval": sum(
                1 for item in registered if item["status"] in {"PENDING_CHECKIN", "pending"}
            ),
            "not_joined": len(not_joined),
            "total": len(attended) + len(registered) + len(not_joined),
        },
    }
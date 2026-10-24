import csv
import io
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import activity_helpers as helpers
from ..database import get_db
from ..models import Activity, Attendance, Member, Registration, Task, User
from ..schemas import (
    ActivityCreate,
    ActivityOut,
    ActivityUpdate,
    AttendanceOut,
    AttendanceVerification,
)
from ..security import (
    get_current_user,
    ensure_member_profile,
    is_admin_or_leader,
    is_member,
    require_roles,
)

router = APIRouter(prefix="/activities", tags=["activities"])


def _get_activity_or_404(db: Session, activity_id: int) -> Activity:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Hoạt động không tồn tại")
    return activity


def _serialize(db: Session, activity: Activity, current_user: User) -> ActivityOut:
    return ActivityOut(**helpers.activity_out_payload(db, activity, current_user))


def _as_utc_naive(value: datetime) -> datetime:
    """Normalize incoming aware datetimes to the UTC-naive format used by SQLite."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


@router.get("", response_model=List[ActivityOut])
def list_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách hoạt động (mọi vai trò đều xem được).

    FIX 2: không lọc theo status/club_id/ngày — trả FULL để cả
    Chủ nhiệm và Thành viên đều thấy hoạt động vừa tạo ngay.
    Model hiện tại chưa có cột status nên mặc định mọi bản ghi
    đã lưu là 'published'/hiển thị.
    """
    activities = db.query(Activity).order_by(Activity.start_time.desc()).all()
    return [_serialize(db, a, current_user) for a in activities]


@router.get("/upcoming", response_model=List[ActivityOut])
def upcoming_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Các hoạt động chưa kết thúc, dùng cho trang chủ của Thành viên."""
    from datetime import datetime

    activities = (
        db.query(Activity)
        .filter(Activity.end_time >= datetime.utcnow())
        .order_by(Activity.start_time.asc())
        .limit(limit)
        .all()
    )
    return [_serialize(db, a, current_user) for a in activities]


@router.post("", response_model=ActivityOut, status_code=201)
def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Tạo hoạt động mới — chỉ Chủ nhiệm / Trưởng ban."""
    start_time = _as_utc_naive(data.start_time)
    end_time = _as_utc_naive(data.end_time)
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="Thời gian kết thúc phải sau thời gian bắt đầu")
    activity = Activity(
        title=data.title,
        description=data.description,
        location=data.location,
        start_time=start_time,
        end_time=end_time,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return _serialize(db, activity, current_user)


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chi tiết hoạt động (kèm trạng thái đăng ký / điểm danh của chính mình)."""
    activity = _get_activity_or_404(db, activity_id)
    return _serialize(db, activity, current_user)


@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Chỉnh sửa hoạt động — chỉ Chủ nhiệm / Trưởng ban."""
    activity = _get_activity_or_404(db, activity_id)

    changes = data.model_dump(exclude_unset=True)
    for field in ("start_time", "end_time"):
        if field in changes and changes[field] is not None:
            changes[field] = _as_utc_naive(changes[field])
    if "end_time" in changes and "start_time" in changes:
        if changes["end_time"] <= changes["start_time"]:
            raise HTTPException(status_code=400, detail="Thời gian kết thúc phải sau thời gian bắt đầu")
    elif "end_time" in changes and changes["end_time"] <= activity.start_time:
        raise HTTPException(status_code=400, detail="Thời gian kết thúc phải sau thời gian bắt đầu")
    elif "start_time" in changes and activity.end_time <= changes["start_time"]:
        raise HTTPException(status_code=400, detail="Thời gian kết thúc phải sau thời gian bắt đầu")

    for key, value in changes.items():
        setattr(activity, key, value)
    db.commit()
    db.refresh(activity)
    return _serialize(db, activity, current_user)


@router.delete("/{activity_id}", status_code=204)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chu_nhiem")),
):
    """Xóa hoạt động — chỉ Chủ nhiệm."""
    activity = _get_activity_or_404(db, activity_id)
    db.query(Attendance).filter(Attendance.activity_id == activity_id).delete()
    db.query(Registration).filter(Registration.activity_id == activity_id).delete()
    db.query(Task).filter(Task.activity_id == activity_id).delete()
    db.delete(activity)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Đăng ký tham gia (dành cho Thành viên)
# ---------------------------------------------------------------------------

@router.post("/{activity_id}/register", status_code=201)
def register_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Thành viên đăng ký tham gia hoạt động."""
    from datetime import datetime

    activity = _get_activity_or_404(db, activity_id)
    member = ensure_member_profile(db, current_user)

    if helpers.get_registration(db, activity_id, member.id):
        raise HTTPException(status_code=400, detail="Bạn đã đăng ký hoạt động này rồi")
    if activity.end_time and activity.end_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Hoạt động đã kết thúc, không thể đăng ký")

    registration = Registration(activity_id=activity_id, member_id=member.id)
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {
        "id": registration.id,
        "activity_id": activity_id,
        "member_id": member.id,
        "created_at": registration.created_at,
        "message": "Đăng ký tham gia thành công ✅",
        "registration_count": db.query(Registration)
        .filter(Registration.activity_id == activity_id)
        .count(),
    }


@router.delete("/{activity_id}/register", status_code=200)
def unregister_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Thành viên hủy đăng ký tham gia hoạt động."""
    _get_activity_or_404(db, activity_id)
    member = ensure_member_profile(db, current_user)

    registration = helpers.get_registration(db, activity_id, member.id)
    if not registration:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký hoạt động này")
    if helpers.get_attendance(db, activity_id, member.id):
        raise HTTPException(
            status_code=400,
            detail="Bạn đã điểm danh hoạt động này, không thể hủy đăng ký",
        )

    db.delete(registration)
    db.commit()
    return {"message": "Đã hủy đăng ký tham gia", "activity_id": activity_id}


@router.get("/{activity_id}/registration-status")
def my_registration_status(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trạng thái đăng ký + điểm danh của chính người dùng hiện tại."""
    activity = _get_activity_or_404(db, activity_id)

    if current_user.role == "thanh_vien":
        member = ensure_member_profile(db, current_user)
    else:
        member = db.query(Member).filter(Member.id == current_user.member_id).first() if current_user.member_id else None
    if not member:
        return {
            "activity_id": activity_id,
            "is_registered": False,
            "my_attendance_status": None,
            "can_register": False,
            "can_check_in": False,
            "message": "Không thể truy xuất trạng thái hoạt động cho tài khoản này",
        }

    attendance = helpers.get_attendance(db, activity_id, member.id)
    registered = helpers.get_registration(db, activity_id, member.id) is not None
    window_open = helpers.is_check_in_open(activity)

    return {
        "activity_id": activity_id,
        "member_id": member.id,
        "is_registered": registered,
        "my_attendance_status": attendance.status if attendance else None,
        "my_checked_at": (
            attendance.checked_in_at or attendance.checked_at if attendance else None
        ),
        "check_in_open": window_open,
        "can_register": not registered,
        "can_check_in": registered and (
            attendance is None or attendance.status in {"REJECTED", "rejected"}
        ) and window_open,
        "message": helpers.check_in_window_message(activity),
    }
# ---------------------------------------------------------------------------
# Quản lý đăng ký / điểm danh (dành cho Chủ nhiệm & Trưởng ban)
# ---------------------------------------------------------------------------

@router.get("/{activity_id}/registrations")
def activity_registrations(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Danh sách thành viên đã đăng ký — chỉ Chủ nhiệm / Trưởng ban."""
    _get_activity_or_404(db, activity_id)
    registrations = helpers.registrations_payload(db, activity_id)
    return {
        "activity_id": activity_id,
        "count": len(registrations),
        "checked_in_count": sum(1 for r in registrations if r["checked_in"]),
        "registrations": registrations,
    }


@router.get("/{activity_id}/attendees")
def activity_attendees(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Danh sách người dùng đã điểm danh — chỉ Chủ nhiệm / Trưởng ban."""
    _get_activity_or_404(db, activity_id)
    attendees = helpers.attendees_payload(db, activity_id)
    return {
        "activity_id": activity_id,
        "count": len(attendees),
        "attendees": attendees,
    }


@router.get("/{activity_id}/participants")
def activity_participants(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách thành viên chia 3 trạng thái cho thành viên và ban quản lý.

    - attended: Đã điểm danh (kèm attended_at = thời gian điểm danh).
    - registered: Đã tham gia nhưng chưa điểm danh / đang chờ duyệt / bị từ chối.
    - not_joined: Chưa tham gia.
    Thành viên chỉ nhận link ảnh minh chứng của chính họ; người quản lý xem được toàn bộ.
    """
    _get_activity_or_404(db, activity_id)
    data = helpers.participants_payload(db, activity_id, include_proofs=current_user.is_admin_or_leader)
    return {"activity_id": activity_id, **data}


@router.patch("/{activity_id}/verify-attendance")
def verify_activity_attendance(
    activity_id: int,
    data: AttendanceVerification,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Duyệt hoặc từ chối ảnh minh chứng điểm danh."""
    _get_activity_or_404(db, activity_id)
    record = (
        db.query(Attendance)
        .filter(
            Attendance.activity_id == activity_id,
            Attendance.member_id == data.member_id,
            Attendance.status == "PENDING_CHECKIN",
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt điểm danh đang chờ duyệt")

    from datetime import datetime

    record.status = "ATTENDED" if data.action == "approve" else "REJECTED"
    record.verified_by = current_user.id
    record.verified_at = datetime.utcnow()
    record.reject_reason = (data.reject_reason or "").strip() if data.action == "reject" else ""
    db.commit()
    db.refresh(record)
    return {
        "activity_id": record.activity_id,
        "member_id": record.member_id,
        "status": record.status,
        "proof_image_url": record.proof_image_url,
        "checked_in_at": record.checked_in_at or record.checked_at,
        "verified_by": record.verified_by,
        "verified_at": record.verified_at,
        "reject_reason": record.reject_reason,
    }


# --- Alias đúng yêu cầu: POST /api/activities/:id/join & /checkin ---
# (tương đương register / attendance/check-in hiện có, thêm cho dễ nhớ)
@router.post("/{activity_id}/join", status_code=201)
def join_activity_alias(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Alias của POST /activities/{id}/register: Thành viên nhấn Tham gia."""
    return register_activity(activity_id, db, current_user)


@router.post("/{activity_id}/checkin", response_model=AttendanceOut, status_code=201)
async def checkin_activity_alias(
    activity_id: int,
    photo: UploadFile = File(...),
    feedback: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_member),
):
    """Nộp điểm danh kèm ảnh minh chứng."""
    from .attendance import submit_check_in

    return await submit_check_in(activity_id, photo, feedback, db, current_user)


@router.get("/{activity_id}/attendees/export")
def export_attendees(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin_or_leader),
):
    """Xuất báo cáo điểm danh ra file CSV — chỉ Chủ nhiệm / Trưởng ban."""
    activity = _get_activity_or_404(db, activity_id)
    attendees = helpers.attendees_payload(db, activity_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["STT", "Họ tên", "MSSV", "Trạng thái", "Phản hồi", "Thời gian điểm danh"])
    for index, row in enumerate(attendees, start=1):
        writer.writerow(
            [
                index,
                row["full_name"],
                row["student_id"],
                row["status_label"],
                row["feedback"],
                row["checked_at"].strftime("%d/%m/%Y %H:%M") if row["checked_at"] else "",
            ]
        )

    buffer.seek(0)
    filename = f"diem_danh_hoat_dong_{activity_id}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )